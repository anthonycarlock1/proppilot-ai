# Automated EKS release

The `deploy-eks` job in [Application containers](../.github/workflows/containers.yaml) runs only on `main`, after tests, publication and published-container verification succeed. Pull requests do not get AWS deployment credentials. Cloud deployments are serialized and are not cancelled while another release is applying.

## Identity and bootstrap

The dedicated `anthony-proppilot-github-deploy` role trusts GitHub's existing OIDC provider for audience `sts.amazonaws.com` and the exact subject `repo:anthonycarlock1@237302030/proppilot-ai@1435163725:ref:refs/heads/main`. This repository uses GitHub immutable OIDC subjects containing owner/repository IDs; its API reports `use_immutable_subject: true`. Names-only trust does not match. No AWS keys are stored as GitHub secrets. The job requests a 30-minute session and verifies the expected account. See [GitHub's official AWS OIDC guide](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws).

The AWS policy permits describing only the existing assessment cluster and publishing/reading only the five PropPilot application ECR repositories. ECR authorization requires a wildcard resource; repository operations remain scoped. The role cannot manage IAM, Terraform state, SageMaker models/endpoints, DynamoDB, nodes or clusters. Application AWS calls use the separate Pod Identity roles, not the deployment role.

The existing cluster uses `CONFIG_MAP` authentication. Administrator bootstrap adds a `proppilot-deployers` group mapping for this role to `aws-auth`, retaining the original node mapping. A namespaced Role permits application Deployment/Service/ConfigMap writes, pod/rollout reads and temporary port-forward creation. It does not permit Secret reads, service-account writes, other-namespace writes or cluster resource creation. Deployment rights allow running application code within this namespace, so repository main-branch write access remains a trusted privilege.

```bash
terraform -chdir=terraform/ci init -input=false
terraform -chdir=terraform/ci plan -out=ci.tfplan
# Review before applying: two dedicated additions in the initial bootstrap.
terraform -chdir=terraform/ci apply ci.tfplan
.venv/bin/python scripts/bootstrap_ci_access.py
```

This root has its own S3 key `proppilot/ci/terraform.tfstate`. It does not create or manage the account's existing GitHub OIDC provider. The school account denies OIDC provider Get/List; successful role creation does not substitute for a real workflow authentication check. The bootstrap script checks the cluster context and uses resource-version/test guards when appending the mapping. Do not run it under the deployment role; it intentionally needs administrator bootstrap rights.

## Release path

1. Tests and GHCR publication/temporary Compose verification pass for the commit.
2. GitHub exchanges its OIDC token for the scoped deployment session.
3. The job pulls the five published GHCR images, verifies source labels and copies the linux/amd64 runtime images into immutable ECR commit tags. It pulls the ECR images and requires the runtime image IDs to match the tested GHCR sources. OCI index/attestation representation may differ; index-digest equality is not claimed.
4. The job checks real Kubernetes allow/deny decisions using its own identity and dry-runs the application-only `k8s/ci` overlay. This overlay excludes namespace, quota, service accounts, Secret and RBAC bootstrap resources.
5. It applies pinned ECR digests and waits for all five rollouts. Pods keep their existing workload identities and internal handoff Secret.
6. A temporary runner-local port-forward reaches the frontend. A real Chrome test calls Bedrock, both SageMaker endpoints and DynamoDB, explicitly confirms a fictional QA ticket, reloads it and verifies resolved version 3.
7. The job saves identity, permission decisions, image digests, rollout state and live browser evidence as a 14-day artifact. It closes the port-forward; the EKS application stays running.

Each live verification creates one fictional ticket and normally resolves it; a failed test can leave a clearly named QA record at an earlier status. No ticket deletion is performed. These paid model calls are distinct from credential-free PR checks.

## Failure and recovery

An authentication, permission, mirror, dry-run, rollout or browser failure fails the job; it does not return simulated success. Later jobs do not bypass upstream failures. The workflow does not automatically roll back on a cloud-service transient error or incomplete test, because that alone does not prove an application release is bad. Inspect the failing stage, compare the previous verified image/configuration, and use the reviewed [Kubernetes rollback runbook](kubernetes.md) before repeating real verification.

A rerun reuses immutable ECR tags only after comparing runtime image IDs. Concurrent releases serialize at the deployment job. PR writers cannot assume the deployment role, but maintainers of main can change deployment code within the role's scope. OIDC avoids permanent keys; it does not replace repository access controls.

The initial RBAC checks in [ci-rbac-verification.json](ci-rbac-verification.json) used administrator impersonation and server dry-run. Real workflow authentication/deployment evidence must be recorded separately; configuration or bootstrap success alone is not a completed automated deployment.


## Verified execution

[Run 40543770367, attempt 2](https://github.com/anthonycarlock1/proppilot-ai/actions/runs/40543770367/attempts/2) successfully authenticated through OIDC, copied all five runtime images with identity checks, verified all eight Kubernetes permission decisions, passed server dry-run and five rollouts, and passed the real Chrome Bedrock/SageMaker/DynamoDB ticket flow. [Saved evidence](automated-deployment-verification.json), [live browser result](automated-cloud-browser-verification.json) and [release digests](automated-release-images.json) outlive temporary Actions artifacts. Five ready pods had zero restarts after verification; earlier coursework Deployments remained available.

Attempt 1 passed upstream tests/builds/publication/verification but failed at OIDC before changing workloads: its initial legacy names-only trust did not match this repository's immutable subject. A reviewed one-field trust correction retained the exact repository IDs and main branch; only the failed deployment job was rerun. The successful artifact ID is recorded explicitly because reruns can produce identical artifact names across attempts. Initial bootstrap added two IAM resources; the correction updated only the role trust and the final Terraform plan had no changes.
