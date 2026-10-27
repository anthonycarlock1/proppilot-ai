import os
import httpx
from fastapi import HTTPException
from services.tickets.schemas import DraftRequest


class TicketClient:
    def __init__(self, url=None, token=None):
        self.url = (url or os.getenv('TICKETS_SERVICE_URL', 'http://127.0.0.1:8006')).rstrip('/')
        self.token = token or os.getenv('ASSESSMENT_WRITE_TOKEN', '')

    def request(self, method, path, *, payload=None, key=None, params=None):
        headers = {'X-Assessment-Token': self.token} if path == '/assessments' else {}
        if key:
            headers['Idempotency-Key'] = str(key)
        try:
            response = httpx.request(method, self.url + path, json=payload, headers=headers,
                                    params=params, timeout=httpx.Timeout(25, connect=3))
            data = response.json()
        except Exception:
            raise HTTPException(503, 'Ticket service is temporarily unavailable') from None
        if not response.is_success:
            raise HTTPException(response.status_code, data.get('detail', 'Ticket operation failed'))
        return response.status_code, data

    def save_draft(self, text, result):
        assessment = result['tool_results'][0]['result']
        urgency = assessment['urgency_assessment']
        payload = DraftRequest.model_validate({'description': text, 'assessment': {
            'category': assessment['category'], 'category_model_version': assessment['model_version'],
            'category_provider': assessment['provider'], 'urgency': urgency['urgency'],
            'urgency_model_version': urgency['model_version'], 'urgency_provider': urgency['provider'],
            'recommended_priority': urgency['recommended_priority'], 'policy_version': urgency['policy_version'],
            'confirmed_hazards': urgency['confirmed_hazards'], 'escalation_reasons': urgency['escalation_reasons'],
            'manual_review_required': True}}).model_dump()
        return self.request('POST', '/assessments', payload=payload)[1]
