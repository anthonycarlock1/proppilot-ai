# Category SageMaker release

## Status and ownership

Deployed and verified on 2026-10-22: `anthony-proppilot-category-v010` is InService in `us-east-1`. Four real SageMaker predictions passed through the FastAPI wrapper; see [saved evidence](category-sagemaker-verification.json). This verifies hosting/integration, not model reliability. The local Compose service still defaults to local inference.

Terraform created one dedicated ECR repository and five hosting resources. Existing coursework resources were not modified. The AWS account is shared; use only dedicated `anthony-proppilot` resources.

Release image: `388691194728.dkr.ecr.us-east-1.amazonaws.com/anthony-proppilot-category-hosting@sha256:87bfcd599b4c1d130c36f31a3a39f14d118a053cab95edcef7edf4bbd5143339`. Immutable release tag: `category-v010-20261022`.

## Hosting contract

The hosting container runs the category pipeline locally on port 8080, exposes GET/POST `/ping` and POST `/invocations`, and accepts the `serve` argument through an entrypoint that replaces the shell process. Its baked-in artifact is trained in a separate image stage. No S3 model archive is required for this baked-in artifact approach.

The SageMaker image uses root as required by AWS's documented container contract; the application wrapper remains non-root. See [AWS custom inference container guidance](https://docs.aws.amazon.com/sagemaker/latest/dg/your-algorithms-inference-code.html).

Build locally from the project root:

```bash
docker build --platform linux/amd64 -f ml/serving/Dockerfile -t proppilot-category-hosting:dev .
docker run -d --name proppilot-category-hosting-check -p 127.0.0.1:8082:8080 proppilot-category-hosting:dev serve
curl http://127.0.0.1:8082/ping
curl http://127.0.0.1:8082/invocations -H 'Content-Type: application/json' -d '{"text":"The toilet is clogged."}'
docker rm -f proppilot-category-hosting-check
```

## Cloud release sequence

Anthony identified the AWS account as school-funded. Keep the initial footprint to on-demand hosting and avoid creating another cluster. Verify account identity and inspect each saved plan before applying. Initial single-developer deployment uses ignored local state; preserve it and migrate to protected remote state before shared or CI infrastructure execution. Neither root manages a VPC, EKS cluster, or existing coursework resources.

1. In `terraform/registry`, run `terraform init`, then `terraform plan -out=registry.tfplan`. Review and apply that saved plan to create only the dedicated immutable ECR repository.
2. Authenticate Docker to the repository's registry using `aws ecr get-login-password --region us-east-1` piped to `docker login --username AWS --password-stdin <registry-host>`. Never put credentials in source or image layers.
3. Tag and push the hosting image with a unique release tag. Read its registry digest with `aws ecr describe-images`. Use the `repository@sha256:...` URI for deployment.
4. In `terraform/hosting`, run `terraform init` and `terraform plan -var='image_uri=<digest-uri>' -out=hosting.tfplan`. Review and apply the saved plan. It creates a dedicated execution role/policy, model, 2-GB serverless endpoint configuration (maximum concurrency 2), and endpoint. No provisioned concurrency is configured.
5. Verify endpoint InService and make a real prediction with `aws sagemaker-runtime invoke-endpoint --region us-east-1 --endpoint-name anthony-proppilot-category-v010 --content-type application/json --body '{"text":"The toilet is clogged."}' --cli-binary-format raw-in-base64-out /tmp/proppilot-category-prediction.json`.
6. Give the calling workload `sagemaker:InvokeEndpoint` only on the endpoint ARN. The hosting root outputs a policy document but does not attach it to existing users or cluster roles.
7. Run the wrapper with `MODEL_PROVIDER=sagemaker`, `AWS_REGION=us-east-1`, and `CATEGORY_SAGEMAKER_ENDPOINT=anthony-proppilot-category-v010`. Local processes can use an authorized AWS profile; cloud workloads should use workload identity. Do not bake keys into Docker images.

The initial resource name includes version v010. Plan a distinct release identity for future model versions rather than assuming application deployment updates hosted models.

## Provider behavior

The application wrapper defaults to `local`. In `sagemaker` mode `/ready` validates configuration only, explicitly reporting `remote_connectivity_checked=false`; it does not invoke a paid remote prediction. Only a real `/predict` smoke test proves endpoint access. Successful wrapper responses identify provider `sagemaker` and retain the hosted model version.

The adapter has a 3-second connection timeout, 70-second read timeout, and no automatic retries in this first release. Cold-start failures may require a later client retry. Failed calls or malformed upstream responses return sanitized 502 errors; missing configuration returns 503. There is no local fallback. Hosted probabilities are validated for labels, range, sum, and consistency with the selected category.

## Teardown

Inspect a destroy plan in `terraform/hosting` before destroying only this project's endpoint/model/configuration/role. Supply the same image URI when Terraform requests it. Preserve evidence first. Then explicitly remove only this project's ECR image versions before reviewing a destroy plan in `terraform/registry`; repository force deletion is disabled. Do not destroy earlier assessment or class resources.

Repeat real-cloud verification from the project root with `.venv/bin/python scripts/verify_sagemaker_category.py`. It requires authorized AWS credentials and `httpx==0.28.1` for FastAPI TestClient. The saved evidence identifies the actual path: an in-process HTTP test client invoking the wrapper, followed by real SageMaker Runtime calls. It does not claim Kubernetes, browser, or Bedrock integration.
