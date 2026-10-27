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

This is a temporary runner integration deployment. Placeholder credentials mean it cannot invoke Bedrock, SageMaker or DynamoDB; the ticket liveness check does not establish storage readiness. Real AWS integration evidence remains separate. No EKS rollout or production deployment is claimed by this workflow. Existing AWS resources and the local running staging stack are unaffected.

## Run and inspect

```bash
gh run list --workflow containers.yaml --repo anthonycarlock1/proppilot-ai
gh run view RUN_ID --repo anthonycarlock1/proppilot-ai --log-failed
```

A manual workflow dispatch on `main` reruns checks/publication/verification for that commit. A dispatch on another branch runs tests only. Review the run's conclusion and artifacts; a workflow file by itself is not proof that publication worked. The GitHub account needs Actions minutes/package storage allowance for this private repository.

The next deployment milestone must configure scoped GitHub-to-AWS identity, Kubernetes workload identity and GHCR pull access, then verify the live cloud path. Do not upload development AWS credentials or the local assessment token to repository secrets as a shortcut. Kubernetes rollback should select a previously verified image digest and rerun rollout/cloud checks; this workflow does not yet automate that rollout.
