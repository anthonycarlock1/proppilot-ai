"""Contract checks for inference, input validation, and missing-artifact behavior."""
import unittest
from fastapi.testclient import TestClient
from services.category.app import create_app


class CategoryTests(unittest.TestCase):
    def test_prediction_and_validation(self):
        with TestClient(create_app()) as client:
            self.assertEqual(client.get('/health').status_code, 200)
            self.assertEqual(client.get('/ready').status_code, 200)
            result = client.post('/predict', json={'text': 'The air conditioner is not cooling.'})
            self.assertEqual(result.status_code, 200)
            body = result.json()
            self.assertEqual(body['category'], 'hvac')
            self.assertEqual(body['provider'], 'local')
            self.assertEqual(set(body['probabilities']), {'hvac', 'plumbing', 'electrical', 'general'})
            self.assertAlmostEqual(sum(body['probabilities'].values()), 1)
            for payload in ({'text': '   '}, {'text': 123}, {'text': 'x' * 4001}, {},
                            {'text': 'sink leaking', 'extra': True}):
                self.assertEqual(client.post('/predict', json=payload).status_code, 422)

    def test_missing_artifact_does_not_claim_readiness(self):
        with TestClient(create_app('/nonexistent/proppilot-model.joblib')) as client:
            self.assertEqual(client.get('/health').status_code, 200)
            self.assertEqual(client.get('/ready').status_code, 503)
            self.assertEqual(client.post('/predict', json={'text': 'sink leaking'}).status_code, 503)
