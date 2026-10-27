"""Verify a running category API using only the Python standard library."""
import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen

base = os.getenv('CATEGORY_URL', 'http://127.0.0.1:8001').rstrip('/')


def request(path, payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    req = Request(base + path, data=body, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=10) as response:
            return response.status, json.load(response)
    except HTTPError as exc:
        return exc.code, json.load(exc)


for path in ('/health', '/ready'):
    status, body = request(path)
    assert status == 200, (path, status, body)

results = []
for text, expected in [
    ('The air conditioner is not cooling.', 'hvac'),
    ('The toilet is clogged.', 'plumbing'),
    ('The electrical outlet is sparking.', 'electrical'),
    ('The front door lock is broken.', 'general'),
]:
    status, body = request('/predict', {'text': text})
    assert status == 200 and body['category'] == expected, (status, body)
    assert abs(sum(body['probabilities'].values()) - 1) < 1e-6
    results.append({'text': text, 'result': body})

for invalid in ({}, {'text': '   '}, {'text': 123}, {'text': 'x' * 4001}):
    status, body = request('/predict', invalid)
    assert status == 422, (status, body)

print(json.dumps({'status': 'passed', 'base_url': base, 'predictions': results,
                  'invalid_requests_checked': 4}, indent=2))
