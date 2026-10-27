import logging
import os
import secrets
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Query, Response
from services.tickets.schemas import CreateTicket, DraftRequest, StatusUpdate
from services.tickets.store import TicketStore, TicketError


def create_app(store=None, draft_token=None):
    app = FastAPI(title='PropPilot Ticket API', version='0.1.0')
    repository = store or TicketStore()
    token = draft_token or os.getenv('ASSESSMENT_WRITE_TOKEN')

    def run(action):
        try:
            return action()
        except TicketError as exc:
            raise HTTPException(exc.status, str(exc)) from None
        except Exception as exc:
            logging.getLogger(__name__).error('Ticket storage operation failed (%s)', type(exc).__name__)
            raise HTTPException(503, 'Ticket storage is temporarily unavailable') from None

    @app.get('/health')
    def health():
        return {'status': 'healthy', 'service': 'tickets'}

    @app.get('/ready')
    def ready():
        run(lambda: repository.client.describe_table(TableName=repository.table))
        return {'status': 'ready', 'storage': 'dynamodb'}

    @app.post('/assessments', status_code=201)
    def save_assessment(payload: DraftRequest, x_assessment_token: str = Header(default='')):
        if not token:
            raise HTTPException(503, 'Assessment handoff is not configured')
        if not secrets.compare_digest(token.encode(), x_assessment_token.encode()):
            raise HTTPException(403, 'Assessment handoff denied')
        return run(lambda: repository.draft(payload.model_dump()))

    @app.post('/tickets', status_code=201)
    def create_ticket(payload: CreateTicket, response: Response, idempotency_key: UUID = Header()):
        ticket, replayed = run(lambda: repository.create(payload.model_dump(mode='json'), str(idempotency_key)))
        response.status_code = 200 if replayed else 201
        return {'ticket': ticket, 'replayed': replayed}

    @app.get('/tickets')
    def list_tickets(limit: int = Query(default=20, ge=1, le=50), cursor: str | None = Query(default=None, pattern=r'^PP-[0-9]{20}-[a-f0-9]{8}$')):
        return run(lambda: repository.list(limit, cursor))

    @app.get('/tickets/{identifier}')
    def get_ticket(identifier: str):
        return run(lambda: repository.get_ticket(identifier))

    @app.patch('/tickets/{identifier}')
    def update_ticket(identifier: str, payload: StatusUpdate):
        return run(lambda: repository.update(identifier, payload.status, payload.expected_version))

    return app


app = create_app()
