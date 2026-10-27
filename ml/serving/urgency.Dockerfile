FROM python:3.11-slim AS dependencies
WORKDIR /build
COPY ml/requirements.lock.txt ml/requirements.lock.txt
COPY services/urgency/requirements.txt services/urgency/requirements.txt
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r services/urgency/requirements.txt

FROM dependencies AS training
COPY ml/data/urgency_seed.csv ml/data/urgency_seed.csv
COPY ml/training/train_urgency.py ml/training/train_urgency.py
RUN /opt/venv/bin/python ml/training/train_urgency.py

FROM python:3.11-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MODEL_PATH=/app/model/urgency.joblib MODEL_PROVIDER=local HOSTING_APP=ml.serving.urgency_app:app
WORKDIR /app
COPY --from=dependencies /opt/venv /opt/venv
COPY --from=training /build/ml/artifacts/urgency-v0.1.0.joblib /app/model/urgency.joblib
COPY services/urgency/app.py services/urgency/app.py
COPY services/urgency/sagemaker.py services/urgency/sagemaker.py
COPY ml/serving/urgency_app.py ml/serving/urgency_app.py
COPY --chmod=755 ml/serving/entrypoint.sh /app/entrypoint.sh
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/ping', timeout=2)"
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["serve"]
