FROM python:3.11-slim AS dependencies
WORKDIR /build
COPY ml/requirements.lock.txt ml/requirements.lock.txt
COPY services/category/requirements.txt services/category/requirements.txt
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r services/category/requirements.txt

FROM dependencies AS training
COPY ml/data/category_seed.csv ml/data/category_seed.csv
COPY ml/training/train_category.py ml/training/train_category.py
RUN /opt/venv/bin/python ml/training/train_category.py

FROM python:3.11-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MODEL_PATH=/app/model/category.joblib
WORKDIR /app
RUN useradd --uid 10001 --create-home appuser
COPY --from=dependencies /opt/venv /opt/venv
COPY --from=training /build/ml/artifacts/category-v0.1.0.joblib /app/model/category.joblib
COPY services/category/app.py /app/services/category/app.py
COPY services/category/sagemaker.py /app/services/category/sagemaker.py
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["uvicorn", "services.category.app:app", "--host", "0.0.0.0", "--port", "8000"]
