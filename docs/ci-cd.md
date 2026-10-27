# Container CI and publication

[Application containers workflow](../.github/workflows/containers.yaml) uses pinned official action commits. Pull requests run separate ML/ticket and agent Python environments, reproduce both synthetic model baselines, build the frontend and run six deterministic browser checks. These checks use mocked external services and no working AWS credentials.

Main-branch pushes run those checks, then build five linux/amd64 multi-stage images in parallel and publish private GHCR packages:

- `ghcr.io/anthonycarlock1/proppilot-ai-category`
- `ghcr.io/anthonycarlock1/proppilot-ai-urgency`
- `ghcr.io/anthonycarlock1/proppilot-ai-tickets`
- `ghcr.io/anthonycarlock1/proppilot-ai-agent`
- `ghcr.io/anthonycarlock1/proppilot-ai-frontend`

Each tag is `sha-<full commit SHA>` with source/revision labels. Only the publish job receives `packages: write`; verification receives `packages: read`. Authentication uses the job's `GITHUB_TOKEN`, not an AWS key or stored registry personal token. This follows [GitHub's official GHCR workflow guidance](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images).

After every publication succeeds, a separate job pulls all five images, verifies their revision labels, resolves content digests and starts a temporary Compose deployment pinned to those digests without building. It checks actual local-model HTTP predictions, nginx-to-agent routing, and the six deterministic browser workflows. Release digests, service status and test artifacts are retained for 14 days. Containers are removed even when verification fails. Commit tags support traceability; they are not an immutable registry policy, and Docker source labels alone are not cryptographic attestations.

The temporary Compose verification job uses placeholder credentials and cannot invoke Bedrock, SageMaker or DynamoDB; its ticket liveness check does not establish storage readiness. After it passes, a separate scoped OIDC job rolls out to EKS and verifies the real cloud path. The local Compose demo is unaffected.

## Run and inspect

```bash
gh run list --workflow containers.yaml --repo anthonycarlock1/proppilot-ai
gh run view RUN_ID --repo anthonycarlock1/proppilot-ai --log-failed
```

A manual workflow dispatch on `main` reruns checks/publication/verification and the gated EKS deployment for that commit. A dispatch on another branch runs tests only. Review the run's conclusion and artifacts; a workflow file by itself is not proof that publication worked. The GitHub account needs Actions minutes/package storage allowance for this private repository.

The manual [EKS deployment](kubernetes.md) now uses scoped workload identities, private ECR images and a verified real-cloud browser path. [Automated deployment](cloud-cd.md) now uses a scoped OIDC role and namespace RBAC, then verifies the real cloud workflow; see [successful execution evidence](automated-deployment-verification.json). Do not upload development AWS credentials or the local assessment token to repository secrets as a shortcut. Kubernetes rollback should select a previously verified image digest and rerun rollout/cloud checks; the cloud job records a failing result and leaves rollback to the reviewed runbook.

## Verified release

[Run 40442879961](https://github.com/anthonycarlock1/proppilot-ai/actions/runs/40442879961) completed successfully for commit `bbaee25105c6b4c9e8d8d49a65d904695ef6f269`: 29 Python tests, six pre-publication browser checks, all five image publications, actual local inference/proxy checks and six published-stack browser checks. All five containers were healthy, and cleanup succeeded. [Saved evidence](container-ci-verification.json) retains the exact five registry digests after temporary Actions artifacts expire. The CI implementation was merged in PR #8; remote state was merged in PR #7.
