"""Verify real hosted urgency predictions and wrapper-side policy."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import boto3
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.urgency.app import create_app
from services.urgency.sagemaker import SageMakerPredictor

ENDPOINT = 'anthony-proppilot-urgency-v010'
REGION = 'us-east-1'


def main():
    session = boto3.Session(region_name=REGION)
    status = session.client('sagemaker').describe_endpoint(EndpointName=ENDPOINT)['EndpointStatus']
    if status != 'InService':
        raise RuntimeError(f'Endpoint is {status}')
    samples = [
        ('There is a small scuff on the hallway wall and it is only cosmetic.', 'low'),
        ('The kitchen faucet drips slowly into the sink; the drain works and there is no flooding.', 'medium'),
        ('The air conditioner stopped cooling and the occupied house is getting very hot.', 'high'),
        ('There is active fire in the kitchen and smoke is filling the room.', 'emergency'),
    ]
    results = []
    with TestClient(create_app(provider='sagemaker', predictor=SageMakerPredictor(ENDPOINT, REGION))) as client:
        for text, expected in samples:
            response = client.post('/predict', json={'text': text})
            response.raise_for_status()
            result = response.json()
            assert result['urgency'] == expected and result['provider'] == 'sagemaker', result
            results.append({'text': text, 'result': result})
        response = client.post('/predict', json={'text': samples[0][0], 'confirmed_hazards': ['gas_odor']})
        response.raise_for_status()
        escalation = response.json()
        assert escalation['urgency'] == 'low' and escalation['recommended_priority'] == 'emergency'
        assert escalation['manual_review_required'] is True
    report = {'verified_at_utc': datetime.now(timezone.utc).isoformat(), 'endpoint': ENDPOINT,
              'region': REGION, 'endpoint_status': status,
              'path': 'FastAPI TestClient -> urgency wrapper -> real SageMaker endpoint; policy applied in wrapper',
              'predictions': results, 'escalation_example': escalation}
    (ROOT / 'docs/urgency-sagemaker-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: four hosted urgency labels and wrapper-side escalation verified')


if __name__ == '__main__':
    main()
