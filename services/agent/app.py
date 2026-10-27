import logging
from uuid import UUID

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from services.agent.orchestrator import MaintenanceAgent, Hazard
from services.agent.tickets import TicketClient
from services.tickets.schemas import CreateTicket, StatusUpdate


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message: str = Field(min_length=3, max_length=4000, strict=True)
    confirmed_hazards: list[Hazard] = Field(default_factory=list, max_length=6)

    @field_validator('message')
    @classmethod
    def clean(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError('Please describe the maintenance issue')
        return value


def create_app(agent=None, tickets=None):
    app = FastAPI(title='PropPilot Agent API', version='0.1.0')
    harness = agent or MaintenanceAgent()
    ticket_client = tickets or TicketClient()

    @app.get('/health')
    def health():
        return {'status': 'healthy', 'service': 'agent'}

    @app.post('/chat')
    def chat(payload: ChatRequest):
        try:
            result = harness.chat(payload.message, confirmed_hazards=payload.confirmed_hazards)
            if result.get('tool_results'):
                try:
                    result['ticket_draft'] = ticket_client.save_draft(payload.message, result)
                except Exception as exc:
                    logging.getLogger(__name__).error('Assessment persistence failed (%s)', type(exc).__name__)
                    result['ticket_draft_error'] = 'Assessment completed, but ticket drafting is unavailable. Please assess again before creating a ticket.'
            return result
        except Exception as exc:
            logging.getLogger(__name__).error('Chat dependency or orchestration failure (%s)', type(exc).__name__)
            raise HTTPException(502, 'Chat is temporarily unavailable; please try again.') from None

    @app.post('/tickets')
    def create_ticket(payload: CreateTicket, idempotency_key: UUID = Header()):
        status, data = ticket_client.request('POST', '/tickets', payload=payload.model_dump(mode='json'), key=idempotency_key)
        return JSONResponse(status_code=status, content=data)

    @app.get('/tickets')
    def list_tickets(limit: int = Query(default=20, ge=1, le=50), cursor: str | None = Query(default=None, pattern=r'^PP-[0-9]{20}-[a-f0-9]{8}$')):
        params = {'limit': limit}
        if cursor:
            params['cursor'] = cursor
        return ticket_client.request('GET', '/tickets', params=params)[1]

    @app.get('/tickets/{identifier}')
    def get_ticket(identifier: str):
        return ticket_client.request('GET', f'/tickets/{identifier}')[1]

    @app.patch('/tickets/{identifier}')
    def update_ticket(identifier: str, payload: StatusUpdate):
        return ticket_client.request('PATCH', f'/tickets/{identifier}', payload=payload.model_dump())[1]

    return app


app = create_app()
