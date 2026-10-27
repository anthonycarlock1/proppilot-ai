"""Local urgency model and explicit, separate priority escalation policy."""
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from typing import Literal

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from services.urgency.sagemaker import SageMakerPredictor

Urgency = Literal['low', 'medium', 'high', 'emergency']
Hazard = Literal['fire_or_smoke', 'gas_odor', 'active_flooding', 'sparking_or_live_wiring', 'structural_collapse', 'carbon_monoxide_alarm']
MODEL_VERSION = '0.1.0'
POLICY_VERSION = '0.1.0'
DEFAULT_MODEL = Path(__file__).resolve().parents[2] / 'ml/artifacts/urgency-v0.1.0.joblib'
LABELS = {'low', 'medium', 'high', 'emergency'}


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str = Field(min_length=3, max_length=4000, strict=True)
    confirmed_hazards: list[Hazard] = Field(default_factory=list, max_length=6)

    @field_validator('text')
    @classmethod
    def clean(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError('Provide at least three non-whitespace characters')
        return value


class ModelPrediction(BaseModel):
    urgency: Urgency
    probabilities: dict[Urgency, float]
    model_version: Literal['0.1.0'] = MODEL_VERSION
    provider: Literal['local', 'sagemaker'] = 'local'

    @model_validator(mode='after')
    def validate_probabilities(self):
        if set(self.probabilities) != LABELS:
            raise ValueError('Expected every urgency label')
        if any(not 0 <= p <= 1 for p in self.probabilities.values()):
            raise ValueError('Invalid probability')
        if abs(sum(self.probabilities.values()) - 1) > 1e-6:
            raise ValueError('Invalid probability sum')
        if self.probabilities[self.urgency] != max(self.probabilities.values()):
            raise ValueError('Inconsistent urgency prediction')
        return self


class PredictionResponse(ModelPrediction):
    recommended_priority: Urgency
    confirmed_hazards: list[Hazard]
    escalation_reasons: list[str]
    policy_version: str = POLICY_VERSION
    manual_review_required: Literal[True] = True


def apply_policy(prediction: ModelPrediction, hazards: list[Hazard]):
    unique = list(dict.fromkeys(hazards))
    return PredictionResponse(**prediction.model_dump(),
        recommended_priority='emergency' if unique else prediction.urgency,
        confirmed_hazards=unique,
        escalation_reasons=[f'Caller-confirmed hazard: {hazard}' for hazard in unique])


def create_app(model_path=None, model=None, provider=None, predictor=None):
    provider = provider or os.getenv('MODEL_PROVIDER', 'local')
    if provider not in {'local', 'sagemaker'}:
        raise ValueError('Unsupported MODEL_PROVIDER')
    @asynccontextmanager
    async def lifespan(app):
        app.state.model = model
        if provider == 'sagemaker':
            app.state.predictor = predictor or SageMakerPredictor(
                os.getenv('URGENCY_SAGEMAKER_ENDPOINT'), os.getenv('AWS_REGION'))
            yield
            return
        if model is None:
            try:
                app.state.model = joblib.load(model_path or os.getenv('MODEL_PATH', str(DEFAULT_MODEL)))
            except Exception:
                logging.getLogger(__name__).error('Urgency model could not be loaded')
        yield
        app.state.model = None

    app = FastAPI(title='PropPilot Urgency API', version=MODEL_VERSION, lifespan=lifespan)

    @app.get('/health')
    def health():
        return {'status': 'healthy', 'service': 'urgency'}

    @app.get('/ready')
    def ready():
        if provider == 'sagemaker':
            if not app.state.predictor.configured():
                raise HTTPException(503, 'SageMaker configuration unavailable')
            return {'status': 'configured', 'provider': provider, 'remote_connectivity_checked': False}
        if app.state.model is None:
            raise HTTPException(503, 'Urgency model unavailable')
        return {'status': 'ready', 'provider': 'local', 'model_version': MODEL_VERSION}

    @app.post('/predict', response_model=PredictionResponse)
    def predict(payload: PredictionRequest):
        if provider == 'sagemaker':
            if not app.state.predictor.configured():
                raise HTTPException(503, 'SageMaker configuration unavailable')
            try:
                raw = app.state.predictor.predict(payload.text)
                if not {'urgency', 'probabilities', 'model_version', 'provider'} <= raw.keys():
                    raise ValueError('Incomplete hosted prediction')
                prediction = ModelPrediction.model_validate(raw)
                prediction = prediction.model_copy(update={'provider': 'sagemaker'})
                return apply_policy(prediction, payload.confirmed_hazards)
            except Exception as exc:
                logging.getLogger(__name__).error('Urgency SageMaker inference failed (%s)', type(exc).__name__)
                raise HTTPException(502, 'Urgency SageMaker inference unavailable') from None
        if app.state.model is None:
            raise HTTPException(503, 'Urgency model unavailable')
        try:
            current = app.state.model
            values = current.predict_proba([payload.text])[0]
            probabilities = {str(label): float(value) for label, value in zip(current.classes_, values)}
            prediction = ModelPrediction(urgency=max(probabilities, key=probabilities.get),
                                         probabilities=probabilities)
            return apply_policy(prediction, payload.confirmed_hazards)
        except Exception:
            logging.getLogger(__name__).error('Urgency inference failed')
            raise HTTPException(503, 'Urgency inference unavailable') from None

    return app


app = create_app()
