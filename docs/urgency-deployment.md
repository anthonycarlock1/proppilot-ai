# Urgency hosting and dual-model chat

Deployed and verified on 2026-10-26. `anthony-proppilot-urgency-v010` is InService. Real tests covered all four hosted labels, wrapper-side escalation, and browser chat using both model endpoints. An initial browser call received an urgency ModelError and a later retry passed; startup logs contained successful invocations without a Python traceback. This does not establish the exact cause. Blanket retries are not enabled; inference errors remain visible, and no local fallback is used.

The urgency release uses a separate `terraform/urgency-hosting/` state root and dedicated `anthony-proppilot-urgency-v010` endpoint in `us-east-1`. The category endpoint's hosting state and image are unchanged. Initial infrastructure execution remains single-developer with ignored local state; migrate to protected remote state before infrastructure CI.

## Release resources

- ECR: `anthony-proppilot-urgency-hosting` (immutable tags).
- Image tag: `urgency-v010-20261026`.
- Image digest: `sha256:436b821d8cbb79b8c2e71d5007268035b6d49625e7fc5b5c7cc06f441d9e404a`.
- Hosting role: `anthony-proppilot-urgency-hosting`, scoped to its image and endpoint logs.
- SageMaker model, endpoint configuration, endpoint: `anthony-proppilot-urgency-v010`.
- On-demand serverless: 2048 MB, maximum concurrency 2, no provisioned concurrency.

The registry plan added one repository; the separate hosting plan adds five resources. Both plans have zero changes/deletions. No other student's resources are managed here.

## Reproduce the initial release

1. Verify AWS identity and review a plan in `terraform/registry`. Apply the saved plan only after review. That root owns both PropPilot repositories.
2. Build from the project root: `docker build --platform linux/amd64 --provenance=false -f ml/serving/urgency.Dockerfile -t proppilot-urgency-hosting:dev .`.
3. Test the image's port 8080 `/ping` and `/invocations` contract locally. It accepts `serve`, runs its baked-in model locally, and never invokes another endpoint. The image uses root as required by the SageMaker container contract; application wrappers run non-root.
4. Authenticate Docker to ECR with a password pipe, push a unique immutable release tag, and read its registry digest. Never put credentials in source or build layers.
5. In `terraform/urgency-hosting`, run `terraform init`, then `terraform plan -var='image_uri=<urgency-repository@sha256:digest>' -out=hosting.tfplan`. Review the plan and apply the saved file. State is stored in the protected S3 backend; see [state and recovery](terraform-state.md). Keep state and plans outside Git.
6. Wait for endpoint InService. Run `.venv/bin/python scripts/verify_sagemaker_urgency.py` from the project root. It tests all four labels through the wrapper against real SageMaker, plus escalation without changing the original model output. The samples verify integration, not generalization.

## Local cloud-integrated processes

Run the category API as documented in the category release guide on port 8003. Run the urgency API in another terminal:

```bash
MODEL_PROVIDER=sagemaker AWS_REGION=us-east-1 \
URGENCY_SAGEMAKER_ENDPOINT=anthony-proppilot-urgency-v010 \
.venv/bin/uvicorn services.urgency.app:app --host 127.0.0.1 --port 8005
```

Run the agent:

```bash
AWS_REGION=us-east-1 CATEGORY_SERVICE_URL=http://127.0.0.1:8003 \
URGENCY_SERVICE_URL=http://127.0.0.1:8005 \
.venv-agent/bin/uvicorn services.agent.app:app --host 127.0.0.1 --port 8000
```

Use authorized host profiles for local development. The calling workload needs `sagemaker:InvokeEndpoint` on both dedicated endpoint ARNs. Hosting execution roles are separate from invocation permissions. Future EKS workloads should use workload identity, not static keys in manifests.

Start the frontend with `docker compose up -d --build frontend` and open http://127.0.0.1:8080. The standalone Compose urgency service on port 8002 remains a local-inference option; cloud chat uses port 8005.

## Assessment semantics

Bedrock selects `assess_maintenance`. LangChain invokes category and urgency APIs concurrently using the original user description. Both outputs must validate; any failure stops the assessment without returning a partial success. The agent allows one assessment and two Bedrock turns, keeping the expected timeout budget below the 240-second frontend limit.

Confirmed hazard flags are validated request data supplied by the user. They are not LLM tool arguments. The urgency wrapper applies escalation after hosted inference, retains the original urgency/probabilities, and requires manual review. The agent rejects changed hazard confirmations or inconsistent policy outputs.

The frontend shows category, model urgency, recommended priority, and manual-review status. A confirmed hazard can raise priority to emergency; it cannot make the model probability into a validated confidence score. No ticket is created.

## Verification and teardown

Real urgency evidence is saved by `verify_sagemaker_urgency.py` to `docs/urgency-sagemaker-verification.json`. `scripts/verify_chat.py` requires both SageMaker providers. The opt-in browser test also asserts both providers and saves `docs/frontend-verification.json`. Treat these as dated evidence, not ongoing health checks.

To remove urgency hosting only, inspect and apply a destroy plan in `terraform/urgency-hosting`, supplying the release image URI. This does not own category hosting. Do not destroy the registry root to remove only urgency: that root now owns both repositories. Image deletion and repository changes must explicitly preserve any retained category release. Preserve verification evidence before teardown.
