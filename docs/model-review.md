# Model review and evaluation status

## What has been reviewed

Anthony agreed on 2026-10-27 to three provisional category rules: AC drain leaks are HVAC, roof leaks are general maintenance, and water-heater failures are plumbing. This is partial policy review, not approval of all 144 seed examples, all challenge labels, or operational readiness. The general urgency-policy question is still pending. Machine-readable scope: [review-status.json](../ml/evaluation/review-status.json).

The AI-assisted audit inspected both seed datasets and added a frozen 32-case labeled diagnostic suite plus eight unscored ambiguous/unsupported cases. The cases/protocol were committed before scoring in commit `8a0cad9`. No model retraining, threshold selection, label correction or endpoint redeployment was performed after seeing the results.

## Results and limits

| Model | Original 16-case macro F1 | Additional 32-case macro F1 | Additional accuracy |
| --- | --- | --- | --- |
| Category | 0.803 | 0.747 | 75.0% |
| Urgency | 0.937 | 0.830 | 84.4% |

The urgency model matched eight provisional emergency labels, missed two cases by one priority level, and over-prioritized three cases, including a cosmetic grille-paint issue as emergency. Some disagreements involve provisional label boundaries that need review. Eight emergency examples are too few and too biased to establish emergency reliability. The original held-out predictions reproduced with the existing local artifacts; their hashes were unchanged during evaluation.

This additional suite is AI-authored after baseline weaknesses were known. It is separate from training, but not independently authored, blind or representative. Exact normalized overlap was rejected; semantic overlap is neither excluded nor measured reliably by nearest-training cosine similarity. Local artifacts are not claimed byte-identical to separately built hosted images. The [full report](../ml/evaluation/challenge-v1-results.json) records provenance, hashes, every prediction, per-class metrics, confusion matrices, priority errors, similarity diagnostics and unscored outputs. The [readable report](../ml/evaluation/challenge-v1-report.md) highlights disagreements and label-review issues.

## Human decisions still needed

| Item | Review needed |
| --- | --- |
| General urgency policy | Confirm or revise the proposed low/medium/high/emergency definitions; no legal SLA or safety claim implied |
| All seed and challenge rows | Review the actual description and label, not just the aggregate score |
| `challenge-general-03` / `low-train-04` | Is a torn secure window screen low or medium, and what context distinguishes them? |
| `challenge-electrical-04` | Is a broken dimmer with normal lighting low or medium? |
| `challenge-general-06` / `medium-train-14` | How does an alternative safe exit affect access-door urgency? |
| `challenge-hvac-02` and similar cosmetic cases | Classify by affected equipment or the repair trade/finish? |
| `high-train-10` | Review the provisional ceiling-sagging label; absence of fallen material is not a safety assessment |

Keep version 1 cases/results as published. If a label is wrong, record the human decision and rationale and create a versioned correction; do not silently change the label after viewing predictions. Policy approval does not by itself validate individual labels or calibrate probabilities.

## A genuinely independent evaluation

Anthony or a qualified reviewer should author fresh fictional cases without seeing model predictions, assign labels/reasons using an agreed policy, and document ambiguities before scoring. Include held-out scenario families and realistic distributions, not only balanced template variations. Authoring after seeing this model's known errors can be useful targeted testing but is not a blind independent benchmark. Use no private tenant records without an appropriate data process.

Keep new test cases out of training/tuning. If the models are expanded, create a separate validation partition for feature/hyperparameter choices and reserve a fresh reviewed test set for final evaluation. Agree quantitative acceptance criteria before evaluating that test set. Do not infer a production confidence cutoff from these synthetic probabilities.

## Reproduce the diagnostic

With the existing trusted baseline artifacts available:

```bash
.venv/bin/python ml/evaluation/evaluate_challenge.py
```

The script refuses uncommitted v1 case/protocol edits, rejects exact overlap/duplicates, verifies original holdout predictions and input hashes, and checks artifact hashes before/after. It runs locally with no AWS requests. Training instructions in [ml/README.md](../ml/README.md) reproduce local baselines if artifacts are absent; training is a separate operation and should not be used to tune this suite. Software/version/seed provenance still needs to be checked when reproducing on another machine.

Every prediction continues to require human review. This milestone provides honest diagnostic evidence; issue #5 remains open for human review and independent evaluation.
