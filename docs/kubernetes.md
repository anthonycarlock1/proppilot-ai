# PropPilot on the existing EKS cluster

Target: `anthony-assessment4-eks`, account `388691194728`, region `us-east-1`, Kubernetes 1.34. All capstone resources use namespace `proppilot`. Do not destroy or import the existing cluster, nodes, networking, add-ons or earlier coursework workloads into capstone Terraform.

## Components and identity

Five Deployments and ClusterIP Services run one replica each. ConfigMap supplies endpoint names, service URLs and region. An opaque Secret supplies only the internal assessment handoff token. AWS credentials are not stored in Kubernetes Secrets. Backend service accounts use separate EKS Pod Identity roles for the category endpoint, urgency endpoint, Nova Lite, or DynamoDB table. Frontend has no AWS role. Trust conditions bind each role to this cluster/namespace/service account, and EC2 metadata credential fallback is disabled.

The existing Pod Identity agent is reused. AWS SDK versions exceed the documented minimum, and use their default credential chain. The service accounts disable automatic Kubernetes API token mounting; the EKS admission webhook separately projects the Pod Identity token. References: [AWS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html), [trust conditions](https://docs.aws.amazon.com/eks/latest/userguide/pod-id-role.html), [SDK requirements](https://docs.aws.amazon.com/eks/latest/userguide/pod-id-minimum-sdk.html).

All pods run non-root, drop Linux capabilities, disallow privilege escalation and use RuntimeDefault seccomp. The namespace enforces the restricted Pod Security profile. Resource requests/limits and a namespace quota bound placement; one replica is a portfolio footprint, not high availability. Startup/liveness checks test process health. Readiness checks validate model configuration and actual DynamoDB DescribeTable access; model readiness does not invoke SageMaker. The real assessment is the model connectivity check. Agent/frontend readiness uses local health rather than cascading dependency checks.

For manual releases, application images are rebuilt from committed source and stored in five private ECR repositories with immutable tags. Kubernetes pins recorded digests. These ECR artifacts are separate builds from the GHCR runner release; do not claim they are identical mirrored artifacts. EKS nodes use existing ECR pull permissions, avoiding a private GHCR personal-token Secret. `docs/eks-images.json` records that initial manual release. The automated pipeline instead copies verified GHCR runtime images, checks runtime image IDs and records current release digests in `docs/automated-release-images.json`.

## Deploy

Prerequisites: authorized AWS profile, Docker, Terraform 1.10+, kubectl matching the cluster, available node capacity and the existing Pod Identity agent. This account restricts OIDC provider Get/List; Pod Identity does not require OIDC provider setup.

```bash
aws eks update-kubeconfig --region us-east-1 --name anthony-assessment4-eks
terraform -chdir=terraform/runtime init -input=false
terraform -chdir=terraform/runtime plan -out=runtime.tfplan
# Review the plan; initial runtime bootstrap adds 17 dedicated resources.
terraform -chdir=terraform/runtime apply runtime.tfplan
.venv/bin/python scripts/publish_ecr.py
.venv/bin/python scripts/deploy_eks.py
```

The publisher refuses uncommitted application source changes, verifies the AWS account, uses the full commit SHA as the immutable release tag, and updates the image digest inventory. ECR login uses a short-lived registry token through stdin. The deployer checks the exact kube context, creates the namespace, generates the assessment token in memory only if the Secret is absent, dry-runs the manifests on the server and waits for all rollouts. It preserves an existing token. Do not print Secret contents or projected credential files.

The first deployment requires the Terraform roles/associations before pods start. The runtime root has its own protected remote state at `proppilot/runtime/terraform.tfstate` in the existing capstone state bucket.

## Access and verify

```bash
kubectl -n proppilot get deployments,pods,services,resourcequota
kubectl -n proppilot port-forward service/frontend 8081:8080 --address 127.0.0.1
```

Open http://127.0.0.1:8081. Port 8080 remains the local Compose demo. No load balancer, DNS or new cluster is provisioned. The application remains an unauthenticated fictional-data demo; a localhost port-forward is the access path for this milestone.

In another terminal:

```bash
cd frontend
PROPPILOT_LIVE_TEST=1 FRONTEND_URL=http://127.0.0.1:8081 PROPPILOT_EVIDENCE_PATH=../docs/eks-browser-verification.json npx playwright test --grep 'real browser request'
```

This calls real Bedrock, both SageMaker endpoints and DynamoDB through the EKS frontend and creates one fictional QA ticket, then resolves it and verifies version 3 after reload. Save EKS-specific evidence; do not overwrite history and describe it as both local and cluster verification. Check restart counts and the application namespace's warning events after the test. Existing coursework Deployments should retain availability.

## Rollback, failures and teardown

For a failed rollout, inspect `kubectl -n proppilot describe pod POD` and sanitized application logs; never dump secrets/environment. Common issues: image pull permissions, Pod Identity association/trust propagation, insufficient node pod slots, AWS endpoint access, and DynamoDB readiness failures. A configuration-ready model wrapper still needs an actual prediction to establish IAM/connectivity.

Review previous image digests/configuration before rollback. `kubectl -n proppilot rollout undo deployment/NAME` restores a previous Deployment revision only; ConfigMap/Secret changes are separate. Pin the reviewed digest/configuration in source and repeat live verification. An old working pod can remain available during a failed rolling update.

To stop capstone workloads, review `kubectl delete namespace proppilot`; it removes only that namespace's workloads and internal token. It does not delete tickets, hosted models, images or the cluster. Runtime Terraform destroy removes scoped role associations/roles and empty ECR repositories; nonempty repositories intentionally block deletion. Review a destroy plan and image retention before teardown. Keep shared cluster infrastructure and the state backend. No destructive teardown or rollback is part of the verification claim.

[Automated cloud deployment](cloud-cd.md) is now verified: a scoped main-only OIDC role copies the tested runtime images into ECR, applies the application-only overlay and runs the real cloud browser lifecycle. The manual bootstrap path remains available. Long-lived AWS credentials are not stored in GitHub. The shared manifests now live in `k8s/base`; `k8s/ci` excludes bootstrap resources.

## Verification evidence

[Cluster and identity evidence](eks-verification.json), [real browser/cloud result](eks-browser-verification.json), and [exact deployed image digests](eks-images.json) record this milestone. All five pods became ready with zero restarts. Agent/ticket startup probes initially saw connection-refused before their servers began listening; probes recovered normally. Each backend reported the container credential provider and its dedicated assumed role. The runtime Terraform follow-up plan had no changes. The real browser flow left one additional clearly fictional resolved QA ticket. Earlier coursework deployments remained available after verification.
