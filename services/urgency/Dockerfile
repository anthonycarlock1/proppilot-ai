FROM python:3.11-slim AS dependencies
WORKDIR /build
COPY ml/requirements.lock.txt ml/requirements.lock.txt
COPY services/urgency/requirements.txt services/urgency/requirements.txt
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r services/urgency/requirements.txt

FROM dependencies AS training
COPY ml/data/urgency_seed.csv ml/data/urgency_seed.csv
COPY ml/training/train_urgency.py ml/training/train_urgency.py
RUN mkdir -p ml/evaluation && /opt/venv/bin/python ml/training/train_urgency.py

FROM python:3.11-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MODEL_PATH=/app/model/urgency.joblib
WORKDIR /app
RUN useradd --uid 10001 --create-home appuser
COPY --from=dependencies /opt/venv /opt/venv
COPY --from=training /build/ml/artifacts/urgency-v0.1.0.joblib /app/model/urgency.joblib
COPY services/urgency/app.py services/urgency/app.py
COPY services/urgency/sagemaker.py services/urgency/sagemaker.py
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["uvicorn", "services.urgency.app:app", "--host", "0.0.0.0", "--port", "8000"]
