# Architecture decisions

Status: initial proposal; implementations are not yet present.

1. Use Python 3.11, FastAPI, and Pydantic for backend services. Use React/TypeScript/Vite for the frontend. Pin compatible dependencies when each component is implemented.
2. The agent API also serves as the frontend backend. Avoid an additional gateway initially.
3. Use LangChain and `langchain-aws` with a tool-capable Bedrock model verified in the AWS account. Bound tool iterations; validate tool arguments and outputs.
4. Train two independent scikit-learn pipelines, starting with TF-IDF and logistic regression. Category and urgency use distinct SageMaker endpoints and FastAPI wrappers with `/health` and `/predict`.
5. Local reproducible training followed by SageMaker hosting is the initial interpretation of the rubric. Confirm if instructor guidance requires SageMaker training jobs.
6. Use DynamoDB for durable tickets. Ticket creation requires confirmation and an idempotency key. Predictions are advisory; deterministic hazard escalation may raise final priority, with its reason recorded separately from model output.
7. Use Docker Compose locally and a separate staging configuration; deploy the complete application to Kubernetes. Prefer a permitted shared EKS cluster; Minikube satisfies the stated Kubernetes requirement if EKS is unavailable.
8. Use GHCR for application images and ECR for SageMaker hosting. Every deployable gets a multi-stage Dockerfile, explicit configuration, and health checking.
9. Keep project-owned Terraform state separate from earlier assessments. Prefer versioned S3 state and native lockfiles with a compatible Terraform release; confirm bonus equivalence to the rubric's DynamoDB locking example.
10. Prefer GitHub OIDC and EKS workload identity over static AWS keys. Do not commit secrets or store AWS keys in images/manifests.

## Reuse candidates

Adapt the Assessment IV SageMaker adapter, typed API responses, request-ID logging, hosting container contracts, Kubernetes probes, workload identity, and deployment verification patterns. Replace domain-specific schemas and artifacts. Existing single-stage Python Dockerfiles need multi-stage replacements. Existing AWS resource availability has not been checked.

## Cost and operational constraints

AWS region is `us-east-1`. Avoid creating another EKS cluster until shared infrastructure is checked. Account for worker nodes, load balancers, NAT, logs, storage, Bedrock tokens, and hosting. On-demand SageMaker serverless is the initial hosting choice; handle cold starts explicitly. Budget and model access must be established before paid deployment.

## Deferred work

Authentication/public production exposure, multi-tenant authorization, external vendor integrations, rent collection, voice, retrieval augmentation, and additional ML endpoints. The initial demo uses fictional data in a controlled environment.
