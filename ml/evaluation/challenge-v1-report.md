# Additional frozen-baseline diagnostic results

AI-authored synthetic challenge v1; all case labels remain provisional. Not independently authored, blind, representative or a safety validation. No model was trained or deployed in this evaluation.

| Task | Original holdout macro F1 (16 cases) | Additional macro F1 (32 cases) | Additional accuracy |
| --- | --- | --- | --- |
| category | 0.803 | 0.747 | 75.0% |
| urgency | 0.937 | 0.830 | 84.4% |

Urgency: 8 provisional emergency cases, recall 100%; 2 lower-priority predictions and 0 two-or-more-level under-priority predictions. These are raw model outputs, without confirmed-hazard overrides. Eight successes do not establish emergency reliability.

## Every scored disagreement

| Task / case | Provisional label | Prediction | Text |
| --- | --- | --- | --- |
| category: challenge-hvac-02 | hvac | general | The ventilation grille paint is flaking; airflow and room temperatures are unchanged. |
| category: challenge-hvac-04 | hvac | plumbing | The AC condensate drain leaves a small contained puddle in its catch tray; cooling still works and water is not spreading. |
| category: challenge-hvac-08 | hvac | general | Thick smoke is pouring from the operating furnace into the occupied hallway. |
| category: challenge-plumbing-01 | plumbing | electrical | The decorative faucet cap has faded, but the tap operates normally without any leak. |
| category: challenge-electrical-02 | electrical | hvac | A socket faceplate is discolored from old paint, with no heat, damage or loss of function. |
| category: challenge-electrical-03 | electrical | hvac | One installed reading light will not turn on; the other lights work and there is no heat or smoke. |
| category: challenge-electrical-07 | electrical | general | The breaker cabinet is smoking and its wiring is visibly glowing red right now. |
| category: challenge-general-01 | general | electrical | There is a small paint scuff on the bedroom wall and the wall is otherwise sound. |
| urgency: challenge-hvac-02 | low | emergency | The ventilation grille paint is flaking; airflow and room temperatures are unchanged. |
| urgency: challenge-hvac-03 | medium | high | The bedroom air vent damper is jammed closed; the other rooms still receive conditioned air and no hazard is reported. |
| urgency: challenge-electrical-04 | medium | low | The hallway dimmer no longer adjusts brightness, but the light stays on normally with no reported hazard. |
| urgency: challenge-general-03 | medium | low | A single window insect screen is torn; the window itself closes and locks securely. |
| urgency: challenge-general-04 | medium | high | Rainwater seeps slowly through the roof into one bucket; the leak is contained and no sagging or electrical contact is reported. |

## Unsupported inputs: diagnostic outputs only

Neither model has an unknown/abstain class. Every input below receives a forced label; the table is not accuracy evidence and does not demonstrate that the agent safely clarifies every case.

| Case | Category output | Urgency output | Why review is needed |
| --- | --- | --- | --- |
| unscored-01 | general | medium | Insufficient detail: affected system and severity unspecified. |
| unscored-02 | general | high | Multiple independent systems; single-category label is inadequate. |
| unscored-03 | general | medium | Rental pricing is outside the maintenance classifiers. |
| unscored-04 | general | medium | Scheduling request without an issue description; no dispatch capability. |
| unscored-05 | hvac | medium | Insufficient observable maintenance details. |
| unscored-06 | plumbing | medium | Alarm type and hazard state require clarification. |
| unscored-07 | hvac | high | System condition, temperature and context are missing. |
| unscored-08 | general | emergency | Historical resolved hazard differs from an active hazard; current status needs review. |

## Label-review issues found during inspection

- `challenge-general-03` labels a torn secure window screen medium, while `low-train-04` labels a tiny torn secure screen low. Degree/context may differ, but the boundary is underspecified. One reported under-priority error may be a provisional-label disagreement rather than an established model failure.
- `challenge-electrical-04` labels a broken dimmer medium although normal lighting is retained; low versus medium needs human clarification.
- `challenge-general-06` labels a jammed access door with another safe exit high; compare `medium-train-14`, where another exit is usable. The distinction between limited inconvenience and lost essential function needs review.
- Cosmetic paint/cover damage on HVAC or electrical equipment needs an explicit rule: classify by affected asset or by repair trade/finish? Anthony approved three particular category rules, not every boundary.
- `high-train-10` describes a sagging ceiling without fallen material. Its high label is provisional, not evidence that lack of fallen debris rules out an immediate hazard.

These issues were identified after scoring. V1 labels/results are preserved. Do not silently relabel cases to improve reported scores; collect human decisions and version any corrections with rationale.

## Interpretation and next step

The false emergency on ventilation-grille paint and category confusions show that small bag-of-words baselines can respond to surface vocabulary while missing system identity or context. Similarity diagnostics in the JSON report expose nearest training examples but are not proof of data independence. Counts, hashes, original-holdout reproduction, confusion matrices, per-class metrics and all outputs are retained in [the full report](challenge-v1-results.json).

Keep manual review and explicit confirmed-hazard handling. Do not add an unvalidated confidence cutoff or retrain against this challenge. Obtain human policy/case review, then a fresh independently authored test set before making a stronger quality claim. See [protocol](challenge-protocol.md) and [review status](review-status.json).
