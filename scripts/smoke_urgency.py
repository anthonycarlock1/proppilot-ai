"""Exercise the running local urgency API; no cloud calls."""
import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen

base = os.getenv('URGENCY_URL', 'http://127.0.0.1:8002').rstrip('/')


def request(path, payload=None):
    req = Request(base + path, data=None if payload is None else json.dumps(payload).encode(),
                  headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=10) as response:
            return response.status, json.load(response)
    except HTTPError as exc:
        return exc.code, json.load(exc)


for path in ('/health', '/ready'):
    status, result = request(path)
    assert status == 200, (path, status, result)

results = []
for text, expected in (
    ('There is a small scuff on the hallway wall and it is only cosmetic.', 'low'),
    ('The kitchen faucet drips slowly into the sink; the drain works and there is no flooding.', 'medium'),
    ('The air conditioner stopped cooling and the occupied house is getting very hot.', 'high'),
    ('There is active fire in the kitchen and smoke is filling the room.', 'emergency'),
):
    status, result = request('/predict', {'text': text})
    assert status == 200, (status, result)
    assert result['urgency'] == expected, result
    assert result['manual_review_required'] is True
    assert abs(sum(result['probabilities'].values()) - 1) < 1e-6
    results.append(result)

status, ordinary = request('/predict', {'text': 'The paint has a cosmetic scuff.'})
assert status == 200
status, escalated = request('/predict', {'text': 'The paint has a cosmetic scuff.',
                                        'confirmed_hazards': ['gas_odor']})
assert status == 200
assert escalated['urgency'] == ordinary['urgency']
assert escalated['recommended_priority'] == 'emergency'
assert escalated['escalation_reasons']

for invalid in ({'text': '   '}, {'text': 'A leak', 'confirmed_hazards': ['unknown']}):
    status, _ = request('/predict', invalid)
    assert status == 422, status

print(json.dumps({'status': 'passed', 'predictions': results,
                  'hazard_escalation_preserves_model_output': True}, indent=2))
