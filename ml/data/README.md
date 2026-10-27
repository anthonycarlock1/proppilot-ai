# Category seed dataset

`category_seed.csv` contains 64 fictional, AI-authored examples created for this project: 48 training and 16 fixed test examples, balanced across four labels. No external dataset or tenant records were used. These examples are project-authored seed material, not a licensed third-party benchmark. Human review is pending.

## Label policy

- `hvac`: heating, ventilation, air conditioning, thermostats, and associated equipment/drains.
- `plumbing`: water supply, drainage, sewage, fixtures, and water heaters.
- `electrical`: wiring, circuits, outlets, switches, and lighting fixtures.
- `general`: building envelope, doors, windows, finishes, flooring, cabinetry, and pests.

Choose the affected system, not merely a symptom. An AC drain leak is HVAC; a roof leak is general. A water heater belongs to plumbing for this dataset, even though it may use electricity. Urgency is a separate task: an electrical issue is not automatically an emergency, and general maintenance can be hazardous.

Multiple independent issues, ambiguous appliance failures, and unfamiliar requests are outside this initial single-label dataset. The future application must ask for clarification or manual review instead of treating every prediction as authoritative.

## Splits and review

The split is fixed before baseline training. `scenario_group` keeps related examples in one partition; future paraphrases must retain their source scenario's group and split. Current groups contain one example each. Validation rejects exact normalized duplicates, but semantic duplicates still require human inspection.

Review labels and assumptions before expanding the dataset. Do not adjust examples or hyperparameters repeatedly to improve this test score. Add a separate validation partition for tuning and a fresh untouched test set for later evaluation.

## Limits

This is a deliberately small development seed, not representative property-management data. Its vocabulary, class balance, and labels reflect the authoring assumptions. Test metrics measure only this synthetic holdout. A larger independently reviewed dataset and real-world validation are needed before relying on predictions operationally.
