import time
import unittest
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient
from botocore.exceptions import ClientError
from services.tickets.app import create_app
from services.tickets.store import TicketStore, TicketError, wire


ASSESSMENT = {'category': 'hvac', 'category_model_version': '0.1.0', 'category_provider': 'sagemaker',
    'urgency': 'high', 'urgency_model_version': '0.1.0', 'urgency_provider': 'sagemaker',
    'recommended_priority': 'high', 'confirmed_hazards': [], 'escalation_reasons': [],
    'policy_version': '0.1.0', 'manual_review_required': True}


class TicketApiTests(unittest.TestCase):
    def test_internal_handoff_requires_token(self):
        store = Mock()
        store.draft.return_value = {'assessment_id': str(uuid4())}
        payload = {'description': 'The AC is not cooling.', 'assessment': ASSESSMENT}
        with TestClient(create_app(store, 'test-token')) as client:
            self.assertEqual(client.post('/assessments', json=payload).status_code, 403)
            self.assertEqual(client.post('/assessments', json=payload, headers={'X-Assessment-Token': 'test-token'}).status_code, 201)
        store.draft.assert_called_once()

    def test_explicit_review_valid_key_and_server_assessment_required(self):
        store = Mock()
        payload = {'assessment_id': str(uuid4()), 'property_label': 'Demo property', 'confirm_reviewed': True}
        key = {'Idempotency-Key': str(uuid4())}
        store.create.return_value = ({'ticket_id': 'example'}, False)
        with TestClient(create_app(store)) as client:
            self.assertEqual(client.post('/tickets', json=payload).status_code, 422)
            for value in (False, 1, 'true'):
                self.assertEqual(client.post('/tickets', json={**payload, 'confirm_reviewed': value}, headers=key).status_code, 422)
            self.assertEqual(client.post('/tickets', json={**payload, 'category': 'electrical'}, headers=key).status_code, 422)
            self.assertEqual(client.post('/tickets', json=payload, headers=key).status_code, 201)
            store.create.return_value = ({'ticket_id': 'example'}, True)
            result = client.post('/tickets', json=payload, headers=key)
            self.assertEqual(result.status_code, 200)
            self.assertTrue(result.json()['replayed'])

    def test_storage_failure_and_status_conflict_remain_visible(self):
        store = Mock()
        store.list.side_effect = RuntimeError('private AWS error')
        store.update.side_effect = TicketError(409, 'Ticket changed; refresh before updating')
        with TestClient(create_app(store)) as client:
            response = client.get('/tickets')
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('private', response.text)
            self.assertEqual(client.patch('/tickets/example', json={'status': 'resolved', 'expected_version': 1}).status_code, 409)
            self.assertEqual(client.patch('/tickets/example', json={'status': 'resolved', 'expected_version': True}).status_code, 422)


class TicketStorageTests(unittest.TestCase):
    def payload(self):
        return {'assessment_id': str(uuid4()), 'property_label': 'Demo property', 'unit': '', 'confirm_reviewed': True}

    def test_missing_and_expired_assessments_cannot_create_tickets(self):
        for draft, expected in (({}, 404), ({'Item': wire({'expires_at': int(time.time()) - 1})}, 410)):
            client = Mock()
            client.get_item.side_effect = [{}, draft]
            with self.assertRaises(TicketError) as error:
                TicketStore(client, 'test-table').create(self.payload(), str(uuid4()))
            self.assertEqual(error.exception.status, expected)
            client.transact_write_items.assert_not_called()

    def test_creation_is_one_atomic_transaction_with_unique_guards(self):
        client = Mock()
        client.get_item.side_effect = [{}, {'Item': wire({'description': 'The AC is not cooling.',
            'assessment': ASSESSMENT, 'expires_at': int(time.time()) + 100})}, {}]
        store = TicketStore(client, 'test-table')
        result, replayed = store.create(self.payload(), str(uuid4()))
        self.assertFalse(replayed)
        self.assertEqual(result['status'], 'open')
        actions = client.transact_write_items.call_args.kwargs['TransactItems']
        self.assertEqual(len(actions), 4)
        self.assertEqual(sum('Put' in action for action in actions), 3)
        self.assertIn('ConditionCheck', actions[-1])
        self.assertTrue(all(action['Put']['ConditionExpression'] == 'attribute_not_exists(pk)' for action in actions[:3]))

    def test_racing_same_key_recovers_committed_ticket(self):
        import hashlib
        import json
        payload, key = self.payload(), str(uuid4())
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        client = Mock()
        client.get_item.side_effect = [{}, {'Item': wire({'description': 'The AC is not cooling.',
            'assessment': ASSESSMENT, 'expires_at': int(time.time()) + 100})}, {},
            {'Item': wire({'fingerprint': fingerprint, 'ticket_id': 'winner'})},
            {'Item': wire({'ticket_id': 'winner', 'status': 'open', 'version': 1})}]
        client.transact_write_items.side_effect = ClientError({'Error': {'Code': 'TransactionCanceledException'}}, 'TransactWriteItems')
        result, replayed = TicketStore(client, 'test-table').create(payload, key)
        self.assertTrue(replayed)
        self.assertEqual(result['ticket_id'], 'winner')

    def test_key_reuse_and_stale_status_are_rejected(self):
        client = Mock()
        client.get_item.return_value = {'Item': wire({'fingerprint': 'different', 'ticket_id': 'other'})}
        store = TicketStore(client, 'test-table')
        with self.assertRaises(TicketError) as error:
            store.create(self.payload(), str(uuid4()))
        self.assertEqual(error.exception.status, 409)
        client.get_item.return_value = {'Item': wire({'ticket_id': 'other', 'status': 'open', 'version': 2})}
        with self.assertRaises(TicketError) as error:
            store.update('other', 'in_progress', 1)
        self.assertEqual(error.exception.status, 409)
        client.update_item.assert_not_called()

    def test_list_uses_query_pagination_not_scan(self):
        client = Mock()
        client.query.return_value = {'Items': [], 'LastEvaluatedKey': wire({'pk': 'WORKSPACE#demo', 'sk': 'TICKET#last'})}
        result = TicketStore(client, 'test-table').list(10, 'previous')
        self.assertEqual(result['next_cursor'], 'last')
        self.assertTrue(client.query.call_args.kwargs['ConsistentRead'])
        self.assertEqual(client.query.call_args.kwargs['Limit'], 10)
        client.scan.assert_not_called()
