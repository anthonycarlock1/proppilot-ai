# Environment inventory

Checked 2026-10-22. No dependencies installed or cloud resources queried.

| Tool | Observed version/status |
| --- | --- |
| Python | 3.11.15 |
| Node.js | 26.0.0; choose and pin the frontend runtime during implementation |
| npm | 11.12.1 |
| Docker CLI | 28.5.2 |
| Docker daemon | Verified reachable outside the execution sandbox; server 28.5.2. The sandbox itself still blocks socket access. |
| Terraform | 1.15.6 |
| kubectl | 1.34.1; Kustomize 5.7.1 |
| AWS CLI | 2.31.18 |
| GitHub CLI | 2.82.0 |
| Minikube | Not found on PATH |

Read-only AWS checks subsequently confirmed identity access and the three Anthony Assessment IV SageMaker endpoints InService in `us-east-1`. The account also contains other students' resources; inventory is not permission to modify them. Bedrock model access, cluster availability, and GitHub authentication remain unchecked. PropPilot-specific deployment status is recorded separately in `sagemaker-deployment.md`.

Local planning document links passed a filesystem link check. Application tests are not applicable yet.
