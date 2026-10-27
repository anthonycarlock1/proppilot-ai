# Frozen baseline challenge protocol — v1

This is an additional AI-authored diagnostic suite, created after the v0.1.0 baseline results were known. It is separate from training and original holdouts, but it is **not independently authored, human-validated, blind or representative real-world evaluation**. Some cases deliberately target known weaknesses. Human review of every label remains pending; agreement with label rules alone does not approve every example.

Before first scoring, commit the case files and this protocol. Do not retrain, change labels, tune thresholds or select cases after observing predictions. Preserve v1 results and hashes even when results are poor. Corrections require a new suite version with a documented reason; tuning requires a separate validation set and a fresh future test set.

`challenge-v1.csv` has 32 single-issue cases: eight per category and eight per urgency label, with two cases for each category/urgency combination. Categories and urgency follow the existing provisional seed policies. `challenge-unscored-v1.csv` contains eight ambiguous, multi-issue or unsupported inputs without invented ground-truth labels. Do not include those eight in accuracy/F1 or treat their forced predictions as correct answers.

Use existing trusted local category/urgency artifacts. Record their SHA256, input hashes, software version and original-holdout prediction agreement. The local artifacts share the published training procedure/version; this does not establish byte equality with separately built SageMaker artifacts. Do not replace or retrain deployed endpoints in this milestone.

Report separately for each task: accuracy, macro F1, per-class precision/recall/F1/support, confusion matrix and every prediction. For urgency, also report emergency recall, lower-priority errors and errors two or more priority levels below the provisional label. Score raw model output; no caller hazard flags or wrapper overrides are supplied. Report any missed emergency as a diagnostic concern regardless of overall score. Maximum softmax/logistic probabilities are not calibrated confidence and are not a safety gate.

Reject duplicate normalized text/IDs and any exact overlap with either seed dataset. Record nearest training-text cosine similarity using each frozen vectorizer to aid semantic review. Similarity neither proves nor rules out leakage. Related concepts/vocabulary are expected across datasets.

No numeric production acceptance threshold is agreed. This run characterizes weaknesses and does not pass/fail production readiness. Missing human review, small biased synthetic samples and unsupported-input behavior preclude operational reliability claims, even if every prediction is correct.

Independent evaluation remains future work: Anthony or another qualified reviewer should author/label fresh cases without seeing predictions, review disagreements, cover realistic prevalence/context and keep those cases out of tuning. This synthetic challenge does not close that requirement.
