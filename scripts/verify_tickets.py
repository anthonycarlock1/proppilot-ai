"""Real DynamoDB/API verification using a fictional assessment from verify_chat.py."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.tickets.store import TicketStore


def request(path, payload=None, key=None, method=None):
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Idempotency-Key'] = key
    req = Request('http://127.0.0.1:8000' + path,
                  data=None if payload is None else json.dumps(payload).encode(), headers=headers, method=method)
    try:
        with urlopen(req, timeout=35) as response:
            return response.status, json.load(response)
    except HTTPError as exc:
        return exc.code, json.load(exc)


def main():
    draft = json.loads((ROOT / 'docs/chat-verification.json').read_text())['result']['ticket_draft']
    payload = {'assessment_id': draft['assessment_id'], 'property_label': 'Portfolio API Verification (fictional)',
               'unit': 'QA', 'confirm_reviewed': True}
    key = str(uuid4())

    def confirm(_):
        for attempt in range(3):
            status, body = request('/tickets', payload, key)
            if status in (200, 201):
                return status, body
            if status not in (409, 503):
                raise RuntimeError((status, body))
            time.sleep(.15 * (attempt + 1))
        raise RuntimeError((status, body))

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(confirm, range(3)))
    ids = {body['ticket']['ticket_id'] for _, body in results}
    assert len(ids) == 1, results
    ticket_id = ids.pop()
    assert request('/tickets', {**payload, 'property_label': 'Changed property'}, key)[0] == 409
    assert request('/tickets', payload, str(uuid4()))[0] == 409
    assert request('/tickets', {**payload, 'confirm_reviewed': False}, str(uuid4()))[0] == 422
    status, ticket = request(f'/tickets/{ticket_id}')
    assert status == 200 and ticket['version'] == 1
    status, ticket = request(f'/tickets/{ticket_id}', {'status': 'in_progress', 'expected_version': 1}, method='PATCH')
    assert status == 200 and ticket['version'] == 2
    assert request(f'/tickets/{ticket_id}', {'status': 'resolved', 'expected_version': 1}, method='PATCH')[0] == 409
    status, ticket = request(f'/tickets/{ticket_id}', {'status': 'resolved', 'expected_version': 2}, method='PATCH')
    assert status == 200 and ticket['version'] == 3
    persisted = TicketStore().get_ticket(ticket_id)
    assert persisted['status'] == 'resolved' and persisted['assessment_id'] == draft['assessment_id']
    status, page = request('/tickets?limit=1')
    assert status == 200 and len(page['items']) <= 1
    if page['next_cursor']:
        assert request('/tickets?limit=1&cursor=' + page['next_cursor'])[0] == 200
    report = {'verified_at_utc': datetime.now(timezone.utc).isoformat(), 'storage': 'real DynamoDB',
              'ticket': ticket, 'concurrent_confirmations': 3, 'unique_tickets': 1,
              'same_key_changed_payload_rejected': True, 'second_key_same_assessment_rejected': True,
              'stale_update_rejected': True, 'fresh_store_read_persisted': True,
              'note': 'Fictional verification ticket intentionally retained as resolved; no existing records deleted.'}
    (ROOT / 'docs/ticket-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS: concurrency, idempotency, status/version guards and durable read; resolved QA ticket {ticket_id}')


if __name__ == '__main__':
    main()
