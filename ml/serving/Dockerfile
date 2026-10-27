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
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MODEL_PATH=/app/model/category.joblib MODEL_PROVIDER=local
WORKDIR /app
COPY --from=dependencies /opt/venv /opt/venv
COPY --from=training /build/ml/artifacts/category-v0.1.0.joblib /app/model/category.joblib
COPY services/category/app.py services/category/app.py
COPY services/category/sagemaker.py services/category/sagemaker.py
COPY ml/serving/app.py ml/serving/app.py
COPY --chmod=755 ml/serving/entrypoint.sh /app/entrypoint.sh
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/ping', timeout=2)"
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["serve"]
