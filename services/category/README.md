# Category API

By default this service loads the trusted local scikit-learn pipeline once at startup. `/predict` applies the same TF-IDF preprocessing used in training and returns a category and class probabilities. These probabilities are not calibrated confidence scores. Set `MODEL_PROVIDER=sagemaker`, `AWS_REGION=us-east-1`, and `CATEGORY_SAGEMAKER_ENDPOINT` to invoke the hosted model instead; see [deployment instructions](../../docs/sagemaker-deployment.md).

## Run in Docker

From the project root, with Docker running:

```bash
docker compose up -d --build category
curl http://127.0.0.1:8001/ready
curl http://127.0.0.1:8001/predict \
  -H 'Content-Type: application/json' \
  -d '{"text":"The air conditioner is not cooling."}'
```

Interactive API documentation: http://127.0.0.1:8001/docs

Run `python3.11 scripts/smoke_category.py` to check liveness/readiness, predictions for all four categories, and four invalid-input cases against the running service.

Stop the service with `docker compose down`.

The image uses dependency, training, and runtime stages. The model is reproducibly trained inside the build, so a clone does not require an ignored local artifact. Only installed dependencies, the artifact, and serving code enter the final slim image. It runs as a non-root user and binds the published port to localhost. The build requires package-registry access. Base images and transitive API dependencies are not yet fully locked.

## API contract

| Route | Meaning |
| --- | --- |
| `GET /health` | Process liveness; does not imply a usable model |
| `GET /ready` | Model loaded; returns 503 when unavailable |
| `POST /predict` | JSON `text`, 3–4000 characters; returns category, probabilities, model version, local provider |

Missing text, non-string text, blank descriptions, oversized descriptions, and unknown fields return 422. Missing model artifacts and inference failures return sanitized 503 errors. The model path can be configured with `MODEL_PATH`; only use trusted artifacts.

## Local development and tests

Train the baseline first as described in `../../ml/README.md`, then run:

```bash
.venv/bin/python -m pip install -r services/category/requirements.txt httpx==0.28.1
.venv/bin/python -m unittest discover -s tests -p 'test_category.py' -v
.venv/bin/uvicorn services.category.app:app --port 8001
```

In SageMaker mode readiness checks configuration, not live AWS access. Remote failures return 502 without falling back to local inference. GHCR publication, Kubernetes, and full-platform staging Compose remain future milestones.
