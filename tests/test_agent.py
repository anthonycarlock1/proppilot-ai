import unittest
from unittest.mock import Mock

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from services.agent.app import create_app
from services.agent.orchestrator import MaintenanceAgent


def tool_call(name='assess_maintenance'):
    return AIMessage(content='', tool_calls=[{'id': 'call-1', 'name': name,
                     'args': {'text': 'The air conditioner is not cooling.'}}])


class AgentTests(unittest.TestCase):
    def test_draft_failure_does_not_invent_ticket_or_discard_assessment(self):
        harness = Mock()
        harness.chat.return_value = {'reply': 'A real assessment result', 'tool_results': [{'result': {'category': 'hvac'}}]}
        ticket_client = Mock()
        ticket_client.save_draft.side_effect = RuntimeError('private storage details')
        with TestClient(create_app(harness, tickets=ticket_client)) as client:
            response = client.post('/chat', json={'message': 'The AC is not cooling.'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['reply'], 'A real assessment result')
            self.assertIn('ticket_draft_error', response.json())
            self.assertNotIn('ticket_draft', response.json())
            self.assertNotIn('private', response.text)

    def agent(self, replies, predictor=None):
        model = Mock()
        model.bind_tools.return_value.invoke.side_effect = replies
        return MaintenanceAgent(model=model, predictor=predictor or Mock(), urgency_predictor=Mock(return_value={
            'urgency': 'high', 'probabilities': {'low': .1, 'medium': .1, 'high': .7, 'emergency': .1},
            'provider': 'sagemaker', 'model_version': '0.1.0', 'recommended_priority': 'high',
            'confirmed_hazards': [], 'escalation_reasons': [], 'policy_version': '0.1.0',
            'manual_review_required': True}))

    def test_tool_result_then_reply(self):
        predictor = Mock(return_value={'category': 'hvac', 'probabilities': {
            'hvac': .7, 'general': .1, 'electrical': .1, 'plumbing': .1},
            'provider': 'sagemaker', 'model_version': '0.1.0'})
        agent = self.agent([tool_call(), AIMessage(content='The model predicts HVAC.')], predictor)
        with TestClient(create_app(agent, tickets=Mock(save_draft=Mock(return_value={'assessment_id': '00000000-0000-0000-0000-000000000001'})))) as client:
            result = client.post('/chat', json={'message': 'The AC is not cooling.'})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()['tool_results'][0]['result']['provider'], 'sagemaker')
        predictor.assert_called_once_with('The AC is not cooling.')
        agent.urgency_predictor.assert_called_once_with('The AC is not cooling.', [])

    def test_urgency_failure_and_invented_confirmations_fail_closed(self):
        category = {'category': 'hvac', 'probabilities': {'hvac': .7, 'general': .1,
                    'electrical': .1, 'plumbing': .1}, 'provider': 'local', 'model_version': '0.1.0'}
        agent = self.agent([tool_call()], Mock(return_value=category))
        agent.urgency_predictor.side_effect = RuntimeError('urgency unavailable')
        with self.assertRaises(RuntimeError):
            agent.chat('The AC is not cooling.')
        agent = self.agent([tool_call()], Mock(return_value=category))
        value = agent.urgency_predictor.return_value
        value.update(confirmed_hazards=['gas_odor'], recommended_priority='emergency',
                     escalation_reasons=['Caller-confirmed hazard: gas_odor'])
        with self.assertRaises(ValueError):
            agent.chat('The AC is not cooling.')

    def test_greeting_does_not_require_tool(self):
        agent = self.agent([AIMessage(content='What maintenance issue needs attention?')])
        self.assertEqual(agent.chat('Hello')['tool_results'], [])

    def test_confirmed_hazards_are_forwarded_from_request_not_tool_arguments(self):
        category = {'category': 'general', 'probabilities': {'hvac': .1, 'general': .7,
                    'electrical': .1, 'plumbing': .1}, 'provider': 'local', 'model_version': '0.1.0'}
        agent = self.agent([tool_call(), AIMessage(content='Emergency priority requires manual review.')],
                           Mock(return_value=category))
        value = agent.urgency_predictor.return_value
        value.update(confirmed_hazards=['gas_odor'], recommended_priority='emergency',
                     escalation_reasons=['Caller-confirmed hazard: gas_odor'])
        result = agent.chat('The wall has a cosmetic scuff.', confirmed_hazards=['gas_odor'])
        self.assertEqual(result['tool_results'][0]['result']['urgency_assessment']['recommended_priority'], 'emergency')
        agent.urgency_predictor.assert_called_once_with('The wall has a cosmetic scuff.', ['gas_odor'])

    def test_unknown_tool_and_loops_are_bounded(self):
        with self.assertRaises(RuntimeError):
            self.agent([tool_call('delete_property')]).chat('Hello')
        result = {'category': 'hvac', 'probabilities': {'hvac': .7, 'general': .1,
                  'electrical': .1, 'plumbing': .1}, 'provider': 'local', 'model_version': '0.1.0'}
        agent = self.agent([tool_call(), tool_call(), tool_call()], Mock(return_value=result))
        with self.assertRaises(RuntimeError):
            agent.chat('The AC is not cooling.')
        self.assertEqual(agent.predictor.call_count, 1)

    def test_failure_and_bad_input(self):
        agent = self.agent([tool_call()], Mock(side_effect=RuntimeError('private AWS detail')))
        with TestClient(create_app(agent, tickets=Mock(save_draft=Mock(return_value={'assessment_id': '00000000-0000-0000-0000-000000000001'})))) as client:
            result = client.post('/chat', json={'message': 'The AC is not cooling.'})
            self.assertEqual(result.status_code, 502)
            self.assertNotIn('private', result.text)
            for payload in ({'message': '   '}, {'message': 123}, {}, {'message': 'x' * 4001}):
                self.assertEqual(client.post('/chat', json=payload).status_code, 422)
