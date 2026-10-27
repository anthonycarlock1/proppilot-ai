# Rubric evidence checklist

Status updated 2026-10-27. This is an evidence inventory, not an awarded grade. Planned artifacts are not completion evidence.

Verified implementation so far:

- Two independent trained SageMaker endpoints with FastAPI wrappers: `docs/category-sagemaker-verification.json` and `docs/urgency-sagemaker-verification.json`.
- Bedrock/LangChain tool coordinates both model APIs, with greeting/clarification routing and bounded execution: `services/agent/orchestrator.py`.
- React frontend and real browser-to-both-model verification: `docs/frontend-verification.json`.
- Multi-stage Dockerfiles and local Compose for implemented services; registry root and separate hosting roots manage dedicated resources with reviewed Terraform plans.
- Documentation, architecture diagram, and AI critical-evaluation log are maintained incrementally.

Still required: model-data/policy human review and independent evaluation, final reproduction/teardown documentation audit, GitHub Project board, instructor guidance on the solo submission and the recorded presentation. Feature branches, issues and PRs exist; a board needs additional GitHub token scopes. AI assistance is not human team participation.

Additional verified evidence:

- Protected S3 state migration for the original five roots: `docs/remote-state-verification.json`. Runtime and CI roots were later initialized directly in the same protected backend.
- Durable reviewed tickets and real DynamoDB concurrency/persistence: `docs/ticket-verification.json`.
- Five GHCR images and temporary runner integration: `docs/container-ci-verification.json`.
- Manual EKS baseline with scoped Pod Identity: `docs/eks-verification.json` and `docs/eks-browser-verification.json`.
- Complete automated main pipeline, including real OIDC authentication, matching runtime image copies, scoped Kubernetes access, rollout and live cloud browser/ticket verification: `docs/automated-deployment-verification.json` and `docs/automated-cloud-browser-verification.json`.

Both Compose configurations validate; local-model containers were smoke tested and full staging was verified end to end. None of the synthetic model evaluations establish real-world reliability.

| Category | Planned evidence |
| --- | --- |
| Containers | Service multi-stage Dockerfiles, GHCR image tags, development and staging Compose runs |
| Terraform | Variables/outputs, protected remote state, reviewed plans, apply and teardown records |
| CI/CD | Workflow runs showing tests, build, registry push, deployment, rollout and smoke checks |
| LangChain | Tool definitions and trace showing conditional, multi-step orchestration |
| Bedrock/frontend | Live frontend interaction powered by Bedrock with actual capability invocation |
| SageMaker | Training scripts, provenance and evaluations, two endpoint deployments, wrapper `/health` and `/predict`, real invocation results |
| Kubernetes | Namespaces, ConfigMaps, Secrets, probes, rollout and running-service evidence |
| Collaboration | Individual work only; feature branches/issues/PRs can be shown, but human team ownership and peer reviews are unmet pending instructor accommodation |
| Communication | Architecture diagram, reproducible deployment/teardown documentation, video no longer than 15 minutes |
| LLM development | AI-use log with reviewed, tested, adapted, and rejected suggestions |

Do not substitute fabricated reviews, AI agents, or invented collaborators for the rubric's human team requirement.
