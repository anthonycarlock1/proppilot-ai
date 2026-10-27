"""Verify real HTTP chat orchestration and save actual tool results."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

base = os.getenv('AGENT_URL', 'http://127.0.0.1:8000').rstrip('/')
message = 'My tenant says the air conditioner has stopped cooling and the house is very hot. What should I do?'
request = Request(base + '/chat', data=json.dumps({'message': message}).encode(),
                  headers={'Content-Type': 'application/json'})
with urlopen(request, timeout=240) as response:
    result = json.load(response)
assert result['reply'].strip(), result
assert result.get('ticket_draft', {}).get('assessment_id'), 'Trusted ticket draft was not persisted'
assert result['tool_results'], 'Model did not invoke the assessment tool'
assert all(x['result']['provider'] == 'sagemaker' for x in result['tool_results'])
assert result['tool_results'][0]['result']['category'] == 'hvac', result
assert result['tool_results'][0]['result']['urgency_assessment']['provider'] == 'sagemaker'
assert result['tool_results'][0]['result']['urgency_assessment']['manual_review_required'] is True
path = Path(__file__).resolve().parents[1] / 'docs/chat-verification.json'
path.write_text(json.dumps({'verified_at_utc': datetime.now(timezone.utc).isoformat(),
    'path': 'HTTP agent -> Bedrock/LangChain -> category and urgency APIs -> two SageMaker endpoints',
    'message': message, 'result': result}, indent=2) + '\n')
print(json.dumps(result, indent=2))
print(f'PASS: real chat path; evidence saved to {path.name}')
