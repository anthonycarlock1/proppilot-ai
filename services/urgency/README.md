# Urgency API

The second model predicts `low`, `medium`, `high`, or `emergency` from a maintenance description. It uses a separately trained TF-IDF/logistic-regression pipeline. Category predictions do not determine urgency.

The urgency model is deployed as the independent SageMaker endpoint `anthony-proppilot-urgency-v010` and connected to the agent and frontend. See [deployment and verification](../../docs/urgency-deployment.md). The standalone Compose service on port 8002 still defaults to local inference; the cloud-backed wrapper runs on port 8005 in the documented demo setup.

## Train and run

From the project root:

```bash
.venv/bin/python ml/training/train_urgency.py
docker compose up -d --build urgency
python3.11 scripts/smoke_urgency.py
```

Open http://127.0.0.1:8002/docs. The Docker build trains the model in its own stage, so the ignored laptop artifact is not required. The final slim image runs as UID 10001. Compose publishes only on localhost.

Example request:

```json
{
  "text": "The air conditioner stopped cooling and the occupied house is very hot.",
  "confirmed_hazards": []
}
```

## Prediction versus priority policy

The response preserves distinct fields:

- `urgency`: the model's predicted label.
- `probabilities`: uncalibrated model probabilities, not validated confidence scores.
- `recommended_priority`: the model label unless an explicit confirmed hazard raises it to emergency.
- `confirmed_hazards` and `escalation_reasons`: caller-supplied signals and the recorded reason for escalation.
- `model_version`, `policy_version`, and `provider`: provenance.
- `manual_review_required`: always true for this synthetic-data baseline.

Allowed confirmed hazards: `fire_or_smoke`, `gas_odor`, `active_flooding`, `sparking_or_live_wiring`, `structural_collapse`, and `carbon_monoxide_alarm`.

The API does not detect or verify these flags itself. They must reflect an explicit confirmed report; a future chat integration must not invent them. The policy does not rewrite model probabilities, lower an emergency prediction, or claim complete hazard coverage. An empty list means no explicit signals were supplied, not that no hazard exists. Hazard flags are deduplicated.

## Routes and validation

| Route | Meaning |
| --- | --- |
| `GET /health` | Process liveness |
| `GET /ready` | Trusted artifact is loaded; otherwise 503 |
| `POST /predict` | Validated model prediction and separate escalation policy |

Descriptions must be strings of 3–4000 characters and cannot be whitespace-only. Unknown fields and invalid hazards return 422. Missing local artifacts and local inference failures return sanitized 503 errors. In SageMaker mode, missing configuration returns 503, and remote invocation or response-validation failures return 502 without local fallback. `/ready` checks remote configuration only, explicitly not live connectivity. Only trusted joblib files may be loaded through `MODEL_PATH`.

Run tests with `.venv/bin/python -m unittest discover -s tests -p 'test_urgency.py' -v`.

## Model evidence

See [dataset policy](../../ml/data/urgency-README.md) and [evaluation report](../../ml/evaluation/urgency-baseline.json). The initial synthetic holdout has 16 examples: macro F1 0.937, emergency recall 4/4, one under-prioritized medium example, and no errors of two or more levels. The dishwasher failure was predicted low instead of medium. These results do not establish real-world safety or accuracy.

Real-cloud verification covered all four labels and wrapper-side escalation; see `docs/urgency-sagemaker-verification.json`. The combined browser check verifies both hosted providers. Ticket persistence remains the next application component.
