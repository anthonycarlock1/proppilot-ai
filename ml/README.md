# Maintenance category baseline

The first model learns one of four maintenance categories from a description. TF-IDF converts words and word pairs into numeric features. Logistic regression learns which features support each category. Both steps are saved in one pipeline so serving uses the same preprocessing as training.

From the project root:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r ml/requirements.lock.txt
.venv/bin/python ml/training/train_category.py
```

Outputs:

- `ml/artifacts/category-v0.1.0.joblib`: local model pipeline, excluded from Git.
- `ml/evaluation/category-baseline.json`: data hash, dependency version, per-class metrics, confusion matrix, and every held-out prediction.

The command overwrites these outputs on rerun. Only load trusted joblib artifacts; they use Python serialization. `requirements.txt` declares direct dependencies; `requirements.lock.txt` records the full baseline environment. Linux container compatibility will be verified when packaging the inference service.

Read [dataset documentation](data/README.md) before interpreting results. Macro F1 gives each class equal weight. Confusion-matrix rows are expected labels and columns are predictions, in the label order saved in the report. There is no production accuracy gate yet: this milestone verifies a reproducible baseline, not real-world readiness.

The category model is now hosted through its FastAPI wrapper and SageMaker endpoint. See the project README for current deployment status.

## Urgency baseline

Run `.venv/bin/python ml/training/train_urgency.py` to train the independent urgency model. It writes `ml/artifacts/urgency-v0.1.0.joblib` and `ml/evaluation/urgency-baseline.json`. The report includes emergency recall and under-prioritization counts as well as classification metrics. Read [urgency dataset policy](data/urgency-README.md) and [urgency API instructions](../services/urgency/README.md) before interpreting or using it. Its 16-example synthetic holdout is not operational validation.

## Additional frozen-baseline diagnostic

See [the model review](../docs/model-review.md), [frozen protocol](evaluation/challenge-protocol.md) and [results](evaluation/challenge-v1-report.md). Run `.venv/bin/python ml/evaluation/evaluate_challenge.py` against existing trusted artifacts. The 32 labeled and eight unscored AI-authored cases do not constitute independent or human-validated evaluation. No deployed models were retrained for this diagnostic.
