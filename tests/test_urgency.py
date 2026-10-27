import unittest
import io
import json
from unittest.mock import Mock
from fastapi.testclient import TestClient
from services.urgency.app import create_app, ModelPrediction, apply_policy
from services.urgency.sagemaker import SageMakerPredictor


class UrgencyTests(unittest.TestCase):
    def test_remote_response_is_validated_and_policy_runs_in_wrapper(self):
        stream = io.BytesIO(json.dumps({'urgency': 'low', 'probabilities': {
            'low': .7, 'medium': .1, 'high': .1, 'emergency': .1},
            'provider': 'local', 'model_version': '0.1.0'}).encode())
        runtime = Mock()
        runtime.invoke_endpoint.return_value = {'Body': stream}
        predictor = SageMakerPredictor('test-urgency', 'us-east-1', runtime)
        with TestClient(create_app(provider='sagemaker', predictor=predictor)) as client:
            self.assertFalse(client.get('/ready').json()['remote_connectivity_checked'])
            response = client.post('/predict', json={'text': 'A cosmetic mark', 'confirmed_hazards': ['gas_odor']})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['urgency'], 'low')
            self.assertEqual(response.json()['recommended_priority'], 'emergency')
            self.assertEqual(response.json()['provider'], 'sagemaker')
        self.assertTrue(stream.closed)
        sent = json.loads(runtime.invoke_endpoint.call_args.kwargs['Body'])
        self.assertEqual(sent, {'text': 'A cosmetic mark'})

    def test_remote_failure_has_no_local_fallback(self):
        predictor = Mock()
        predictor.configured.return_value = True
        predictor.predict.side_effect = RuntimeError('private AWS detail')
        with TestClient(create_app(provider='sagemaker', predictor=predictor)) as client:
            response = client.post('/predict', json={'text': 'A cosmetic mark'})
            self.assertEqual(response.status_code, 502)
            self.assertNotIn('private', response.text)
        with TestClient(create_app(provider='sagemaker', predictor=SageMakerPredictor(None, None))) as client:
            self.assertEqual(client.get('/ready').status_code, 503)

    def test_confirmed_hazard_raises_priority_without_rewriting_model_output(self):
        prediction = ModelPrediction(urgency='low', probabilities={
            'low': .7, 'medium': .1, 'high': .1, 'emergency': .1})
        result = apply_policy(prediction, ['gas_odor', 'gas_odor'])
        self.assertEqual(result.urgency, 'low')
        self.assertEqual(result.recommended_priority, 'emergency')
        self.assertEqual(result.confirmed_hazards, ['gas_odor'])
        self.assertTrue(result.manual_review_required)
        self.assertEqual(len(result.escalation_reasons), 1)

    def test_no_hazards_does_not_claim_absence_of_danger(self):
        prediction = ModelPrediction(urgency='high', probabilities={
            'low': .1, 'medium': .1, 'high': .7, 'emergency': .1})
        result = apply_policy(prediction, [])
        self.assertEqual(result.recommended_priority, 'high')
        self.assertEqual(result.escalation_reasons, [])
        self.assertTrue(result.manual_review_required)

    def test_local_prediction_and_invalid_inputs(self):
        with TestClient(create_app()) as client:
            self.assertEqual(client.get('/health').status_code, 200)
            self.assertEqual(client.get('/ready').status_code, 200)
            result = client.post('/predict', json={'text': 'There is a small cosmetic scuff on the wall.'})
            self.assertEqual(result.status_code, 200)
            body = result.json()
            self.assertEqual(body['provider'], 'local')
            self.assertEqual(body['urgency'], body['recommended_priority'])
            self.assertAlmostEqual(sum(body['probabilities'].values()), 1)
            hazard = client.post('/predict', json={'text': 'There is a small cosmetic scuff on the wall.',
                                'confirmed_hazards': ['active_flooding']}).json()
            self.assertEqual(hazard['recommended_priority'], 'emergency')
            self.assertEqual(body['urgency'], hazard['urgency'])
            for payload in ({}, {'text': '   '}, {'text': 123}, {'text': 'x' * 4001},
                            {'text': 'A leak', 'confirmed_hazards': ['made_up']},
                            {'text': 'A leak', 'confirmed_hazards': 'gas_odor'},
                            {'text': 'A leak', 'extra': True}):
                self.assertEqual(client.post('/predict', json=payload).status_code, 422)

    def test_missing_model_and_inference_failure(self):
        with TestClient(create_app('/nonexistent/urgency.joblib')) as client:
            self.assertEqual(client.get('/health').status_code, 200)
            self.assertEqual(client.get('/ready').status_code, 503)
            self.assertEqual(client.post('/predict', json={'text': 'A leak'}).status_code, 503)
        model = Mock()
        model.predict_proba.side_effect = RuntimeError('private artifact details')
        with TestClient(create_app(model=model)) as client:
            result = client.post('/predict', json={'text': 'A leak'})
            self.assertEqual(result.status_code, 503)
            self.assertNotIn('private', result.text)

    def test_invalid_probability_distribution_is_rejected(self):
        with self.assertRaises(ValueError):
            ModelPrediction(urgency='low', probabilities={'low': .5, 'medium': .5, 'high': .5, 'emergency': .5})
