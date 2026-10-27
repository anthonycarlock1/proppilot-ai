# Development plan

## Working agreement

Build one component at a time. Explain the component before implementing it; verify its behavior before expanding. Keep documentation and evidence current. Never claim cloud verification from mocked or local tests.

Anthony owns all deliverables and reviews AI suggestions. Deadline, budget, shared-cluster access, dataset choice, and individual-submission accommodation remain unresolved. These do not block local planning and model exploration.

## Milestones

| Phase | Deliverable | Acceptance gate |
| --- | --- | --- |
| 0 | Foundation and environment inventory | Scope, rubric mapping, architecture decisions, tool inventory recorded |
| 1 | Category dataset and baseline | Provenance/license documented; reviewed labels; leakage-aware split; reproducible pipeline; macro F1 and confusion matrix |
| 2 | First vertical slice | Category model hosted in SageMaker; FastAPI wrapper; minimal Bedrock/LangChain chat; container and initial deployment pipeline; real browser-to-model prediction |
| 3 | Urgency model and wrapper | Independent endpoint; held-out evaluation including emergency recall and severe under-prioritization; validated responses |
| 4 | Ticket workflow | Confirmed creation, idempotency, persistent storage, retrieval, status updates; no invented success on failure |
| 5 | Full deployment automation | Multi-stage images; dev/staging Compose; Kubernetes configuration/probes; Terraform lifecycle; GHCR build/push/deploy/verification |
| 6 | Reliability and interface | Bounded tool calls/timeouts; low-confidence clarification; failure tests; readable chat and ticket views |
| 7 | Delivery evidence | Reproduction/teardown runbooks; rubric evidence; presentation under 15 minutes; documented individual-submission limitation |

## Next tasks

- [x] Record tool versions and Docker availability.
- [ ] Confirm assessment deadline and budget with Anthony.
- [ ] Resolve individual-submission grading expectations with the instructor.
- [x] Establish private repository hosting and milestone issues.
- [ ] Create GitHub Project board (token needs project/read:project permissions).
- [ ] Select a licensed maintenance dataset or document a reviewed synthetic-data strategy.
- [x] Define category labels: HVAC, plumbing, electrical, general maintenance (provisional policy documented; human review pending).
- [ ] Define urgency labels with examples: low, medium, high, emergency.
- [ ] Agree on evaluation criteria before reporting model results.
- [x] Train category baseline before implementing its prediction wrapper.

## Verified progress

- Category seed: 64 AI-authored synthetic examples, with human review pending. Baseline macro F1 0.803 on 16 held-out examples; no real-world accuracy claim.
- Category API: local inference, validated request/response contracts, liveness/readiness, non-root multi-stage Docker image, and local Compose HTTP smoke checks.
- SageMaker integration: dedicated hosting image with port 8080 and `/ping`/`/invocations`; configurable wrapper provider; malformed-response and failure handling; seven automated tests passed.
- AWS release is tracked in `docs/sagemaker-deployment.md`; follow live verification evidence rather than assuming a prepared implementation means a deployed endpoint.
- AWS funding: Anthony reports the school pays. No numeric cap has been established; keep the footprint modest and use on-demand hosting.
- First chat slice: Bedrock Nova Lite with bounded LangChain tool calling, category service over HTTP, and real SageMaker result verified. Agent API and multi-stage image implemented; four agent tests passed. Evidence in `docs/chat-verification.json`. Next close the first vertical slice with a minimal React frontend, then proceed to urgency.
- 2026-10-26: React/TypeScript dashboard follows Anthony's supplied visual reference. Session activity, category breakdown, search/filter, and assistant drawer implemented. Three deterministic browser tests passed against the production container; separate real-browser Bedrock/SageMaker test passed and saved `docs/frontend-verification.json`. Frontend container is healthy and non-root. Initial release CI/CD remains pending; urgency model is the next application component.
- 2026-10-26: Independent urgency baseline trained on 64 synthetic examples and tested on 16: macro F1 0.937, emergency recall 4/4, one under-prioritized medium example, no two-level under-prioritization. Local urgency API/container verified with five tests and HTTP smoke checks for all four labels. Policy keeps model urgency separate from recommended priority; explicit caller-confirmed hazards raise priority and every result requires manual review. Next: second SageMaker endpoint, real cloud verification, then agent/frontend integration. Do not report this local service as the second deployed endpoint yet.
- 2026-10-26: Urgency deployed as independent `anthony-proppilot-urgency-v010` endpoint, InService. Reviewed Terraform added one repository and five hosting resources without changes/deletions. Real verification passed all four hosted labels and wrapper-side escalation. Agent now uses one bounded assessment tool to call both services concurrently with the original description. Frontend shows model urgency, recommended priority, and manual-review status; hazard confirmations are explicit request data. Twenty Python tests and four deterministic browser tests passed; a separate browser test verified both hosted providers. Initial urgency ModelError recovered on retry; exact cause is unconfirmed. Next application component: durable maintenance tickets with explicit creation confirmation and idempotency. Infrastructure CI/CD, Kubernetes, remote state, and repository hosting remain separate outstanding milestones.
- 2026-10-26: Durable ticket milestone implemented. Dedicated DynamoDB table created with encryption, recovery and deletion protection. Agent saves trusted 24-hour assessment drafts; users explicitly review and confirm ticket creation. Atomic transaction protects idempotency and one-ticket-per-assessment; status changes use version conditions. UI lists saved tickets, pages records, updates status, and survives reload. Real concurrency check produced one ticket from three confirmations; changed-payload and stale-version writes were rejected. Six deterministic browser tests and the real assess/confirm/reload/start/resolve flow passed. Two fictional QA tickets were retained as resolved. Next: repository/issue organization, complete Compose environments, remote state, CI/CD and Kubernetes deployment; do not add optional product features before closing rubric gaps.

## Validation strategy

Use unit tests for validation and error mapping, integration tests for service contracts and ticket persistence, and real-cloud smoke tests for Bedrock, SageMaker, and deployed application paths. Keep model evaluation separate from software tests. Group related scenarios/paraphrases in one dataset partition. Report synthetic-data limitations explicitly.

Do not provision infrastructure merely to check tooling. Inventory existing cloud resources before choosing new infrastructure. Never destroy shared resources through capstone state.

- 2026-10-26: Private GitHub repository and six milestone issues created. Complete five-service Compose development/staging configurations added with internal DNS, health dependencies and localhost publishing. Staging full browser assessment/create/reload/start/resolve passed against real Bedrock, both SageMaker endpoints and DynamoDB; one additional fictional resolved QA ticket retained. Six deterministic browser tests passed. Project board is blocked by missing GitHub project scopes. Next: protected remote Terraform state, followed by GHCR/CI and Kubernetes.

- 2026-10-26: Protected remote Terraform state implemented in a dedicated private/versioned/encrypted S3 bucket with TLS enforcement and native locking. All five roots migrated after protected local backups; complete resource snapshots/outputs preserved. Terraform reset lineage/serial during migration, recorded explicitly. All five refresh-enabled plans returned zero changes. Real contention test blocked a competing Terraform plan, then the pending operation was cancelled and locks released. Backend bootstrap added six resources only; existing workloads unchanged. Next: application GHCR publication and CI/CD, then Kubernetes.

- 2026-10-26: Container CI/publication milestone verified in GitHub Actions run 40442879961. PR checks and main run passed all 29 Python tests and six deterministic browser tests. Five linux/amd64 images published to private GHCR packages with full-commit tags. Separate runner pulled them, checked revision labels, pinned content digests, started all five healthy services without rebuilding, passed actual local prediction/proxy checks and six browser tests, then removed the deployment. No real AWS calls in CI. Issue 3 remains open for Kubernetes deployment and live-cloud verification. Next: scoped deployment identity, workload identity, private image pull strategy and existing-EKS namespace rollout.

- 2026-10-26: EKS application milestone verified on existing anthony-assessment4-eks, namespace proppilot. Reviewed Terraform added five ECR repositories and four scoped Pod Identity roles/policies/associations (17 additions, no changes/deletions); runtime state starts directly in S3. Five digest-pinned, non-root Deployments have ConfigMap/Secret, quotas, requests/limits and probes. Four actual credential-provider/STS checks verified separate Pod Identity roles without static keys. All five pods became ready with zero restarts; runtime follow-up plan had no changes. Real Chrome test through localhost:8081 reached Bedrock and both SageMaker endpoints, confirmed/persisted/reloaded a ticket and resolved version 3. One additional fictional QA ticket retained. Earlier coursework deployments remain available. Next: automated EKS rollout/live verification through scoped CI identity; model human review/independent evaluation and final deliverables remain.

- 2026-10-27: Automated cloud deployment verified in Actions run 40543770367 attempt 2. Added a main-only short-lived OIDC role with app-ECR/cluster-describe permissions and namespace-scoped RBAC; eight actual permission checks passed, including Secret and cross-namespace denials. CI copied tested GHCR runtime images into ECR and checked image IDs, dry-ran/applied the application overlay, completed five rollouts and passed real Bedrock/both-SageMaker/DynamoDB browser creation/reload/resolution. One fictional QA ticket retained resolved. Initial names-only OIDC trust failed against immutable repository subjects; one reviewed exact-ID trust correction fixed it without broadening access. All five pods ready with zero restarts and earlier workloads available. Next: human dataset/policy review, independent evaluation, final runbook/rubric audit, solo accommodation/Project board and recorded presentation.
