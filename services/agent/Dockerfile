FROM python:3.11-slim AS dependencies
WORKDIR /build
COPY services/agent/requirements.lock.txt requirements.lock.txt
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r requirements.lock.txt

FROM python:3.11-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd --uid 10001 --create-home appuser
COPY --from=dependencies /opt/venv /opt/venv
COPY services/agent/app.py services/agent/app.py
COPY services/agent/orchestrator.py services/agent/orchestrator.py
COPY services/agent/tickets.py services/agent/tickets.py
COPY services/tickets/schemas.py services/tickets/schemas.py
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["uvicorn", "services.agent.app:app", "--host", "0.0.0.0", "--port", "8000"]
