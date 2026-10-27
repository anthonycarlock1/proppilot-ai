import io
import json
import unittest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from services.category.app import create_app
from services.category.sagemaker import SageMakerPredictor
from ml.serving.app import app as hosting_app


class SageMakerTests(unittest.TestCase):
    def test_missing_configuration_is_not_ready(self):
        predictor = SageMakerPredictor(None, None)
        with TestClient(create_app(provider='sagemaker', predictor=predictor)) as client:
            self.assertEqual(client.get('/ready').status_code, 503)
            self.assertEqual(client.post('/predict', json={'text': 'AC not cooling'}).status_code, 503)

    def predictor(self, result):
        stream = io.BytesIO(json.dumps(result).encode())
        client = Mock()
        client.invoke_endpoint.return_value = {'Body': stream}
        return SageMakerPredictor('test-endpoint', 'us-east-1', client), stream, client

    def test_invocation_and_provider(self):
        predictor, stream, runtime = self.predictor({
            'category': 'hvac', 'probabilities': {'hvac': .7, 'general': .1, 'plumbing': .1, 'electrical': .1},
            'provider': 'local', 'model_version': '0.1.0'})
        with TestClient(create_app(provider='sagemaker', predictor=predictor)) as client:
            self.assertFalse(client.get('/ready').json()['remote_connectivity_checked'])
            response = client.post('/predict', json={'text': 'AC not cooling'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['provider'], 'sagemaker')
        self.assertTrue(stream.closed)
        self.assertEqual(runtime.invoke_endpoint.call_args.kwargs['EndpointName'], 'test-endpoint')

    def test_bad_upstream_response_is_rejected(self):
        predictor, stream, _ = self.predictor({'category': 'invented'})
        with TestClient(create_app(provider='sagemaker', predictor=predictor)) as client:
            self.assertEqual(client.post('/predict', json={'text': 'AC not cooling'}).status_code, 502)
        self.assertTrue(stream.closed)

    def test_remote_failure_has_no_local_fallback(self):
        predictor = Mock()
        predictor.configured.return_value = True
        predictor.predict.side_effect = RuntimeError('secret downstream error')
        with TestClient(create_app(provider='sagemaker', predictor=predictor)) as client:
            result = client.post('/predict', json={'text': 'AC not cooling'})
            self.assertEqual(result.status_code, 502)
            self.assertNotIn('secret', result.text)

    def test_hosting_contract_executes_local_model(self):
        with TestClient(hosting_app) as client:
            self.assertEqual(client.get('/ping').status_code, 200)
            self.assertEqual(client.post('/ping').status_code, 200)
            result = client.post('/invocations', json={'text': 'The toilet is clogged.'})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()['category'], 'plumbing')
            self.assertEqual(result.json()['provider'], 'local')
