# Rubric evidence checklist

Status updated 2026-10-26. This is an evidence inventory, not an awarded grade. Planned artifacts are not completion evidence.

Verified implementation so far:

- Two independent trained SageMaker endpoints with FastAPI wrappers: `docs/category-sagemaker-verification.json` and `docs/urgency-sagemaker-verification.json`.
- Bedrock/LangChain tool coordinates both model APIs, with greeting/clarification routing and bounded execution: `services/agent/orchestrator.py`.
- React frontend and real browser-to-both-model verification: `docs/frontend-verification.json`.
- Multi-stage Dockerfiles and local Compose for implemented services; registry root and separate hosting roots manage dedicated resources with reviewed Terraform plans.
- Documentation, architecture diagram, and AI critical-evaluation log are maintained incrementally.

Still required: live-cloud deployment/verification in CI/CD, Kubernetes deployment and configuration, reproducible full-platform lifecycle, GitHub Project/branch/PR evidence, and recorded presentation. Individual-submission grading expectations remain unresolved. Protected S3 state migration is verified for all five Terraform roots with zero-change plans and real lock contention; see `docs/remote-state-verification.json` and the recovery runbook. Persistent reviewed tickets are implemented with real DynamoDB concurrency/persistence evidence in `docs/ticket-verification.json`; the five-service Compose staging stack is verified end to end, but is not a Kubernetes deployment. Both Compose configurations validate; local-model containers were separately smoke tested. Private repository, milestone issues and feature PRs exist; Project board creation needs additional token scopes. Five application images are published to GHCR; CI tests/builds/pushes and verifies a temporary runner Compose deployment. Actual success and image digests are recorded in `docs/container-ci-verification.json`; this is not EKS or real AWS integration verification.

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
