"""Validated category inference through local or SageMaker providers."""
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from typing import Literal

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from services.category.sagemaker import SageMakerPredictor

MODEL_VERSION = '0.1.0'
DEFAULT_MODEL = Path(__file__).resolve().parents[2] / 'ml/artifacts/category-v0.1.0.joblib'
Category = Literal['hvac', 'plumbing', 'electrical', 'general']


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str = Field(min_length=3, max_length=4000, strict=True)

    @field_validator('text')
    @classmethod
    def normalize(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError('Provide at least three non-whitespace characters')
        return value


class PredictionResponse(BaseModel):
    category: Category
    probabilities: dict[Category, float]
    model_version: str
    provider: Literal['local', 'sagemaker']

    @model_validator(mode='after')
    def validate_probabilities(self):
        if set(self.probabilities) != {'hvac', 'plumbing', 'electrical', 'general'}:
            raise ValueError('Expected all four category probabilities')
        if any(not 0 <= value <= 1 for value in self.probabilities.values()):
            raise ValueError('Invalid probability')
        if abs(sum(self.probabilities.values()) - 1) > 1e-6:
            raise ValueError('Probabilities must sum to one')
        if self.probabilities[self.category] != max(self.probabilities.values()):
            raise ValueError('Category must have maximum probability')
        return self


def create_app(model_path=None, provider=None, predictor=None):
    provider = provider or os.getenv('MODEL_PROVIDER', 'local')
    if provider not in {'local', 'sagemaker'}:
        raise ValueError('Unsupported MODEL_PROVIDER')
    @asynccontextmanager
    async def lifespan(app):
        app.state.model = None
        if provider == 'sagemaker':
            app.state.predictor = predictor or SageMakerPredictor(
                os.getenv('CATEGORY_SAGEMAKER_ENDPOINT'), os.getenv('AWS_REGION'))
            yield
            return
        try:
            # Only load trusted, project-created artifacts.
            app.state.model = joblib.load(model_path or os.getenv('MODEL_PATH', str(DEFAULT_MODEL)))
        except Exception:
            logging.getLogger(__name__).error('Category model could not be loaded')
        yield
        app.state.model = None

    app = FastAPI(title='PropPilot Category API', version=MODEL_VERSION, lifespan=lifespan)

    @app.get('/health')
    def health():
        return {'status': 'healthy', 'service': 'category'}

    @app.get('/ready')
    def ready():
        if provider == 'sagemaker':
            if not app.state.predictor.configured():
                raise HTTPException(503, 'SageMaker configuration unavailable')
            return {'status': 'configured', 'provider': provider,
                    'remote_connectivity_checked': False}
        if app.state.model is None:
            raise HTTPException(503, 'Category model unavailable')
        return {'status': 'ready', 'provider': 'local', 'model_version': MODEL_VERSION}

    @app.post('/predict', response_model=PredictionResponse)
    def predict(payload: PredictionRequest):
        if provider == 'sagemaker':
            if not app.state.predictor.configured():
                raise HTTPException(503, 'SageMaker configuration unavailable')
            try:
                result = PredictionResponse.model_validate(app.state.predictor.predict(payload.text))
                return result.model_copy(update={'provider': 'sagemaker'})
            except Exception:
                logging.getLogger(__name__).error('SageMaker inference failed')
                raise HTTPException(502, 'SageMaker inference unavailable') from None
        model = app.state.model
        if model is None:
            raise HTTPException(503, 'Category model unavailable')
        try:
            values = model.predict_proba([payload.text])[0]
            probabilities = {str(label): float(value) for label, value in zip(model.classes_, values)}
            return PredictionResponse(category=max(probabilities, key=probabilities.get),
                                      probabilities=probabilities, model_version=MODEL_VERSION,
                                      provider='local')
        except Exception:
            logging.getLogger(__name__).error('Category inference failed')
            raise HTTPException(503, 'Category inference unavailable') from None

    return app


app = create_app()
