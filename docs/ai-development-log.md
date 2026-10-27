# AI development log

## 2026-10-22 — Scope and foundation

- Tool: Codex / ChatGPT.
- Use: review official instructions, identify reusable Assessment IV patterns, propose architecture and milestones, prepare planning files.
- Human direction: Anthony selected PropPilot AI and an incremental approach, then confirmed he is the sole developer.
- Critical evaluation: prior Assessment IV Python Dockerfiles are single-stage and cannot meet the capstone's multi-stage requirement unchanged. Existing financial models cannot serve as maintenance models. AI assistance cannot satisfy human collaboration requirements.
- Validation: inspected official assessment files and representative previous project source; no application tests or cloud deployment claimed.
- Human review: pending review of the initial planning artifacts.

For subsequent entries, record the suggestion, human review or adaptation, validation performed, and outcome. Preserve meaningful rejected suggestions as evidence.

## 2026-10-22 — Category baseline

- Use: authored 64 fictional labeled examples, training script, dependency pins, and dataset documentation.
- Decision: use a TF-IDF/logistic-regression baseline before building APIs. Synthetic-data strategy is provisional; human label review remains pending.
- Validation: 48 training examples, 16 held-out examples; 13 correct, macro F1 0.803. Dependency consistency passed. Reloaded artifact reproduced all evaluation predictions.
- Critical evaluation: AC drain water, furnace burning smell, and a roof leak were misclassified. The model can confuse symptoms with affected systems. Preserve this test result; do not tune repeatedly against the holdout. Future work needs independent reviewed data and ambiguity handling.
- No cloud deployment or production reliability is claimed.

## 2026-10-22 — Local category API and container

- Use: implemented FastAPI input/output schemas, liveness/readiness, local inference, multi-stage Dockerfile, Compose service, contract tests, and HTTP smoke script.
- Design review: retain probabilities as uncalibrated model outputs; distinguish liveness from loaded-model readiness. Build the artifact in a separate training stage to avoid depending on an untracked laptop file.
- Validation: two unittest cases passed, including malformed inputs and missing-artifact behavior. Docker image built successfully on Linux; synthetic evaluation reproduced macro F1 0.803. Running container passed health/readiness, four category predictions, and four invalid-input HTTP checks. Docker reported healthy; process UID is 10001. Dependency consistency passed.
- Scope: local inference only; SageMaker provider, registry publication, and Kubernetes remain pending. Container remains available on localhost port 8001 for Anthony to inspect.

## 2026-10-22 — SageMaker category release

- Use: built the hosting container, explicit SageMaker provider, probability validation, dedicated Terraform registry/hosting roots, release runbook, and live verification script.
- Human direction: continue cloud integration; Anthony reports AWS is school-funded. Kept scope to one on-demand endpoint with no new cluster.
- Review decisions: separate project resource/state ownership; pin image digest; distinguish configured readiness from live invocation; reject malformed remote results; never silently fall back. Hosting uses root to follow AWS container guidance, while application containers remain non-root.
- Validation: seven automated tests passed; local hosting contract and rebuilt Compose smoke tests passed; Terraform hosting validation and formatting passed. Reviewed plans created one ECR repository and five hosting resources, changing/deleting none. Endpoint InService after about seven minutes. Four real category predictions passed through the FastAPI wrapper; saved evidence in `category-sagemaker-verification.json`.
- Limitation: initial Terraform state is local and ignored; migrate to protected remote state before CI infrastructure execution. Bedrock, frontend, second model, and Kubernetes remain pending. Model data is still a small synthetic seed.

## 2026-10-22 — Bedrock / LangChain category chat

- Use: built the bounded tool-calling harness, chat API, isolated dependency environment/lock, agent Dockerfile, tests, and real HTTP verification script.
- Model: actual Nova Lite invocation confirmed account access before integration; model ID `amazon.nova-lite-v1:0`.
- Critical evaluation: first live response invoked SageMaker correctly but only asked for equipment details. Revised the prompt to give a practical next step before clarification and explicitly label predictions advisory. Repeated the live test and inspected the improved response. No urgency prediction or ticket creation is claimed.
- Validation: four agent unit tests passed (tool execution, greeting route, unknown tool/loop bounds, failure and invalid input). Agent dependency check and Linux image build passed. Real HTTP request traversed Bedrock/LangChain, category HTTP API, and SageMaker and returned the actual hosted prediction; evidence in `chat-verification.json`.
- Limitations: stateless chat; one classifier tool; prompt guidance is not a deterministic hazard policy. Dedicated frontend, urgency, tickets, Kubernetes, and CI releases remain pending. Live demo currently uses host AWS profiles; image contains no credentials.

## 2026-10-26 — Reference-inspired React dashboard

- Human direction: Anthony supplied a dashboard reference and asked to continue progressing. Adapted its sidebar, photo header, cards, activity table, and circular assessment layout to actual current capabilities.
- Use: React/TypeScript interface, same-origin chat client/proxies, responsive styling, multi-stage frontend container, browser tests, design and operating documentation. Used Sites skill guidance for a local preview in the existing AWS capstone repository; no separate hosted Site created.
- Critical evaluation: did not adopt the reference's invented ticket counts, trends, urgent tickets, or 75% triage-confidence claim. Derived session metrics only from real successful responses; ticket metric explicitly unavailable. Replaced confidence chart with category distribution. AI output remains rendered as plain text.
- Validation: production build passed, patched Vite to 8.3.5 after a dependency advisory; npm reports zero known vulnerabilities. Docker image built on Node 22 and served with non-root nginx (UID 101), healthy. Three deterministic browser tests passed for success/activity/filtering, error recovery, and mobile navigation. Initial browser time limit was too short under concurrent cold startup; increased allowance and reran against the production container successfully.
- Cloud verification: initial live request returned 502; both dependencies passed direct follow-up checks and the repeated browser request passed. Cause was not captured by existing sanitized backend logs; do not label it a confirmed cold-start issue. Saved real browser-to-Bedrock/SageMaker evidence in `frontend-verification.json`. UI preserved input on failure and did not add an invented activity entry.
- Limits: local Docker frontend with host-run backends; no EKS deployment, authentication, persistent history, urgency inference, or ticket writes. Session metrics clear on refresh. Background scrolling is locked while the assistant is open. Backend diagnostic logging and transient-failure policy remain reliability follow-ups.

## 2026-10-26 — Local urgency model and service

- Use: authored a separate 80-example synthetic seed, provisional labels, reproducible TF-IDF/logistic-regression training, error analysis, typed API, explicit hazard policy, multi-stage container, and tests.
- Critical evaluation: the synthetic holdout is tiny and shares issue vocabulary with training; emergency recall 4/4 is not evidence of safe real-world emergency detection. Preserved the initial result instead of tuning the holdout. A broken dishwasher without a leak was incorrectly lowered from medium to low. Human dataset review remains pending.
- Design decision: never overwrite the predicted urgency with a rule. Return separate recommended priority and recorded reasons. Explicit caller-confirmed hazards can escalate; absence of flags is not proof of safety. All predictions require manual review. No automatic text-based hazard detector is claimed.
- Validation: five automated urgency tests passed, including invalid inputs, missing model, inference failures, malformed probabilities, and escalation preserving model output. Saved artifact reproduced all 16 evaluation predictions. Docker build reproduced metrics (macro F1 0.937; one under-prioritization, zero severe). HTTP checks covered all four labels, invalid requests, and confirmed-hazard escalation. Container healthy, UID 10001.
- Scope: local urgency service on port 8002 only. No AWS changes in this increment. Category/chat/frontend remain unchanged until the second hosted endpoint and integration are verified.

## 2026-10-26 — Hosted urgency and dual-model assessment

- Use: dedicated urgency hosting image/state, SageMaker adapter, concurrent category/urgency agent tool, user-confirmed hazard fields, priority UI, tests, and release runbook.
- Review decisions: preserve the existing category hosting state; use an immutable urgency image digest. Forward the original report to both models so LLM rewriting cannot remove important context. Keep hazard confirmations outside LLM tool arguments and reject inconsistent returned policy data. Any dependency failure stops the assessment; do not return partial or simulated success.
- Infrastructure: reviewed registry plan added one dedicated repository; reviewed separate hosting plan added five resources, with zero changes/deletions. Endpoint became InService. No class/shared resources modified.
- Validation: category tests 2, category SageMaker tests 5, urgency tests 7, agent tests 6 (20 total), all passed. Four deterministic frontend browser tests passed, including explicit hazard submission and failure recovery. Real urgency verification covered all four labels and a low-model/emergency-policy example. Separate Chrome test passed through Bedrock and both real SageMaker endpoints, returning HVAC/high with manual review required. Evidence in `urgency-sagemaker-verification.json` and updated `frontend-verification.json`.
- Observed failures: one browser run started before the new container was ready and was rerun after startup. An initial real combined request returned urgency ModelError while category succeeded; the same urgency input then succeeded directly and through the browser. CloudWatch startup/invocation logs showed successful responses without an application traceback. Exact transient cause was not established. Retained visible error behavior and did not add indiscriminate retries.
- Limits: models remain synthetic-data baselines; manual review is always required. Local Docker frontend and host-backed APIs are cloud-integrated, not an EKS application deployment. Tickets/persistence, CI/CD, Kubernetes, remote state migration, and individual-submission grading accommodation remain pending.

## 2026-10-26 — Durable tickets and explicit confirmation

- Use: designed the draft/confirmation boundary, DynamoDB single-table keys, transactional duplicate protection, optimistic status updates, ticket API/proxy, review UI, service launcher, and tests/runbook.
- Human direction: proceed with persistent maintenance tickets and explicit creation confirmation. Provisioned one dedicated pay-per-request table from a reviewed Terraform plan (one addition, no changes/deletions); enabled encryption, point-in-time recovery and deletion protection.
- Critical design review: frontend confirmations cannot author model predictions; snapshots come from token-protected agent draft writes. The token is generated in launcher memory and is absent from browser/image/files. Idempotency keys are retained across uncertain saves; changed details cannot silently reuse the key. A second key cannot create another ticket for the same assessment. Draft TTL is checked by the application as DynamoDB deletion is asynchronous.
- Validation: eight ticket tests cover protected handoff, explicit boolean confirmation, API failure mapping, atomic write guards, race replay, key/version conflicts, missing/expired drafts, and Query pagination. Existing agent tests were isolated from ticket networking; an additional test verifies draft-write failure preserves the real assessment without inventing a saved draft. Agent tests total seven. Builds passed for frontend, ticket image, and updated agent image; ticket container liveness/non-root UID 10001 verified.
- Real AWS checks: three concurrent confirmations produced one saved ticket; reuse with changed details, a second key for the assessment, and stale updates were rejected. Fresh storage client read the resolved record. Separate real Chrome test used Bedrock and both SageMaker endpoints, explicitly reviewed/created a ticket, reloaded it, advanced status twice, and reloaded the resolved version 3. Two clearly fictional QA tickets remain as resolved; none of the existing records/resources were deleted.
- UI checks: six deterministic browser tests passed, including confirmation gating, reload behavior, status changes, and stable retry keys. Real-cloud evidence is saved in `ticket-verification.json` and updated `frontend-verification.json`.
- Limits: shared unauthenticated demo; no tenant isolation, vendor dispatch, or conversational session memory. Backend APIs run under the local cloud launcher, not EKS. Full Compose staging, registry publication, infrastructure remote state, CI/CD, Kubernetes, and individual-submission grading accommodation remain pending.


## 2026-10-26 — Complete Compose and GitHub foundation

- Added five-service Compose with internal service DNS, health-based dependencies and localhost-only published ports; staging overlays both existing SageMaker endpoints. Development retains local models, with real Bedrock/DynamoDB in both modes.
- Reviewed credential handling: rejected embedding credentials or an internal token in source or a persistent env file. The launcher snapshots authorized profile credentials into container environments and generates a random shared token. Docker administrators can inspect these; temporary credentials require a restart after refresh. This is local demo credential handling, not Kubernetes workload identity.
- Validation: both configurations passed quiet Compose validation; all five staging services became healthy. Six deterministic browser tests passed. Real browser test passed through the container stack with both hosted predictions, draft persistence, explicit creation, reload, status updates and resolved version 3. One additional fictional QA ticket retained. Development model containers separately verified local predictions; a complete development cloud workflow was not rerun.
- GitHub: created private repository and six milestone issues. Project board request failed due to missing project/read:project token scopes; no board or peer reviews claimed. Initial sandbox authentication failure was resolved by checking with authorized network access.
- Build observation: Docker image export was slow; a read-only disk-usage request returned a transient snapshot-not-found error. Builds and container startup subsequently completed successfully; no cache cleanup or shared Docker changes performed.
- CSV files preserve their original CRLF bytes and evaluation hashes; Git attributes recognize carriage returns at end of CSV lines rather than rewriting source data to satisfy whitespace checks.


## 2026-10-26 — Protected remote Terraform state

- Added dedicated S3 bootstrap root, separate backend keys for all five roots, native lockfiles, versioning, public-access blocks, encryption, bucket ownership and TLS enforcement. Prevent-destroy/no-force-delete safeguards retain state during ordinary teardown. No separate DynamoDB lock table or paid KMS key was necessary.
- Reviewed bootstrap plan: six additions, zero changes/deletions. Applied only that plan. Existing SageMaker, ECR and DynamoDB workload resources were not changed. Fixed the category root's existing stray `l` before `terraform` so it validates.
- Before migration, copied each local state into mode-0600 backups under a mode-0700 gitignored directory. Verified destination keys were absent before copying. Initial registry lineage assertion stopped verification: Terraform reset lineage/serial. Reviewed Terraform's version-specific migration implementation, then required exact full resource/output equality rather than forcing old metadata into remote state. All roots preserved full snapshots and outputs.
- Validation: all five refresh-enabled plans returned detailed exit code zero. Bucket protection and each state object's encryption/version were checked through AWS. A read-only console did not retain a lock; replaced that ineffective test with a real refresh-only apply paused at confirmation using a temporary output. The competing plan was rejected for lock contention. Declined the pending apply, removed temporary output, and verified all lock objects were released. No test output was applied.
- Documentation covers fresh checkout, bootstrap dependency, profile credentials, scoped backend permissions, protected local copies, recovery/force-unlock precautions and keeping backend history during workload teardown. A refresh-only check observed an empty-tags normalization on an ECR resource; it was not applied, and normal plans had no requested resource actions.
- Limits: state access uses the authorized assessment profile. CI identity and workload deployment remain separate milestones. S3 version history is retained and incurs storage/request costs; administrators can deliberately bypass configuration safeguards. No recovery restore or destructive teardown was executed.
