# Urgency seed dataset and label policy

`urgency_seed.csv` contains 80 fictional AI-authored descriptions: 64 training and 16 fixed test examples, balanced across four urgency labels. No external dataset or tenant records were used. This is original project seed material, not a third-party licensed benchmark. Human review is pending.

## Provisional project labels

| Label | Intended meaning | Examples |
| --- | --- | --- |
| `low` | Cosmetic or routine issue, with normal function maintained | Paint scuff, scratched but functioning fixture |
| `medium` | Limited loss of convenience or contained fault, without a reported immediate hazard | Slow contained drip, broken dishwasher without leakage |
| `high` | Essential service, property security, or substantial property condition needs prompt review | No running water, failed heating in cold weather, occupied home overheating |
| `emergency` | Description reports an immediate hazard or uncontrolled damage | Active fire/smoke, gas odor, active flooding, falling structural debris |

These are development triage labels, not response-time guarantees or legally mandated SLAs. Occupant vulnerability, actual temperatures, weather, duration, and local context can change the appropriate response. Those features are not independently modeled in this text-only baseline. Absence of a hazard statement is not proof that a situation is safe.

Urgency and category are independent tasks: electrical requests can be routine, and general maintenance can be an emergency. Do not infer priority solely from category.

## Evaluation and limitations

Use the checked-in split without tuning against its test results. Groups currently identify individual authored scenarios; future variants/paraphrases of a scenario must remain in that scenario's partition. The loader rejects exact normalized duplicates and groups spanning partitions. It does not detect semantic overlap. Related issue types and author vocabulary appear in both partitions, so these metrics are optimistic development evidence, not generalization or emergency-detection validation.

The evaluation reports macro F1, per-class metrics, emergency recall, every prediction, and under-prioritization. Label order is `low`, `medium`, `high`, `emergency`. Under-prioritization means predicting a lower ordinal label; severe under-prioritization means at least two levels lower. Both counts are reported, because even a one-level error can matter.

Before operational use, obtain independently reviewed examples, expand coverage of ambiguous and multi-issue reports, create separate validation/test sets, and evaluate false negatives under realistic conditions. This baseline always requires manual review.
