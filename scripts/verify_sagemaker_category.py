"""Real-cloud verification through the wrapper; run only after endpoint creation."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import boto3
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.category.app import create_app
from services.category.sagemaker import SageMakerPredictor

ENDPOINT = 'anthony-proppilot-category-v010'
REGION = 'us-east-1'


def main():
    session = boto3.Session(region_name=REGION)
    identity = session.client('sts').get_caller_identity()
    endpoint = session.client('sagemaker').describe_endpoint(EndpointName=ENDPOINT)
    if endpoint['EndpointStatus'] != 'InService':
        raise RuntimeError(f"Endpoint is {endpoint['EndpointStatus']}")
    predictor = SageMakerPredictor(ENDPOINT, REGION)
    samples = [
        ('The air conditioner is not cooling.', 'hvac'),
        ('The toilet is clogged.', 'plumbing'),
        ('The electrical outlet is sparking.', 'electrical'),
        ('The front door lock is broken.', 'general'),
    ]
    predictions = []
    with TestClient(create_app(provider='sagemaker', predictor=predictor)) as client:
        for text, expected in samples:
            response = client.post('/predict', json={'text': text})
            if response.status_code != 200:
                raise RuntimeError(f'Wrapper failed: {response.status_code} {response.text}')
            result = response.json()
            if result['provider'] != 'sagemaker' or result['category'] != expected:
                raise RuntimeError(f'Unexpected prediction: {result}')
            predictions.append({'text': text, 'expected': expected, 'result': result})
    report = {'verified_at_utc': datetime.now(timezone.utc).isoformat(),
              'account_id': identity['Account'], 'region': REGION, 'endpoint': ENDPOINT,
              'endpoint_status': endpoint['EndpointStatus'],
              'path': 'FastAPI TestClient -> wrapper -> real SageMaker Runtime -> hosted model',
              'predictions': predictions}
    path = ROOT / 'docs/category-sagemaker-verification.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS: four real SageMaker predictions through the wrapper; evidence: {path.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
