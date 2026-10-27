# Bedrock / LangChain chat API

The chat capability assesses category and urgency through two independent model services. The agent backend also hands off assessment drafts and proxies explicit ticket confirmation/status routes. The LLM does not create tickets autonomously or contact contractors, and conversation memory is not implemented. See `../../docs/urgency-deployment.md` for the dual-model cloud run instructions.

## Request flow

1. FastAPI validates `message` (3–4000 characters, strict string).
2. LangChain sends system instructions, user text, and a tool schema to Amazon Nova Lite through Bedrock Converse.
3. Bedrock can ask a clarifying question or request `assess_maintenance` with structured arguments.
4. The harness validates those arguments and calls category and urgency services concurrently over HTTP, using the original user description.
5. Each service invokes its own SageMaker endpoint when configured for that provider. The urgency wrapper applies its separate escalation policy after model inference.
6. The harness validates both predictions and policy consistency, returns them to Bedrock as a tool result, and asks Bedrock to explain it.

This is tool-calling orchestration, not a fixed keyword response. At most two Bedrock calls and one assessment (two concurrent API calls) occur per request. Unexpected tools, multiple tool calls in one turn, exhausted limits, malformed responses, or dependency failures stop the request with a sanitized 502. No local or invented success is substituted.

`tool_results` exposes executed tool results, not hidden model reasoning. Probabilities are uncalibrated. Prompt instructions guide responses but are not a complete safety or hallucination guarantee. Explicit confirmed-hazard escalation is enforced by the urgency wrapper; automatic hazard detection from text is not claimed.

## Preferred ticket-capable local demo

Run `python3.11 scripts/run_cloud_services.py` from the project root after installing both environments. It starts all four APIs and shares a token in process memory for trusted assessment persistence. Then run the frontend container and follow `services/tickets/README.md`. The individual process commands below are useful for inference-only debugging; without the shared handoff token, ticket draft creation is unavailable.

## Run locally

Use separate virtual environments so LangChain's AWS SDK requirements do not change model-training dependencies. Start from the project root:

```bash
python3.11 -m venv .venv-agent
.venv-agent/bin/python -m pip install -r services/agent/requirements.lock.txt
```

With authorized local AWS credentials, run the SageMaker-backed category API in one terminal:

```bash
MODEL_PROVIDER=sagemaker AWS_REGION=us-east-1 \
CATEGORY_SAGEMAKER_ENDPOINT=anthony-proppilot-category-v010 \
.venv/bin/uvicorn services.category.app:app --host 127.0.0.1 --port 8003
```

Start the urgency wrapper on port 8005 using `docs/urgency-deployment.md`. In another terminal, run the chat API:

```bash
AWS_REGION=us-east-1 BEDROCK_MODEL_ID=amazon.nova-lite-v1:0 \
CATEGORY_SERVICE_URL=http://127.0.0.1:8003 URGENCY_SERVICE_URL=http://127.0.0.1:8005 \
.venv-agent/bin/uvicorn services.agent.app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs and try `POST /chat`:

```json
{"message":"My tenant's air conditioner stopped cooling and the house is very hot. What should I do?"}
```

`GET /health` checks process liveness only. No health check invokes a paid model. There is no remote-readiness guarantee. Each request is independent; conversation history is not persisted.

For development with the local-model category container, run `docker compose up -d category` and set `CATEGORY_SERVICE_URL=http://127.0.0.1:8001`. The result then reports provider `local`; that path is not cloud verification.

## Verification

```bash
.venv-agent/bin/python -m unittest discover -s tests -p 'test_agent.py' -v
python3.11 scripts/verify_chat.py
```

The second command uses the running HTTP APIs and paid AWS inference. It saves `docs/chat-verification.json`, checks an actual category tool execution, and requires both returned providers to be `sagemaker`. It verifies integration on one example, not broad model quality.

## Container and identity

Build from the project root with `docker build -f services/agent/Dockerfile -t proppilot-agent:dev .`. The multi-stage slim image runs as UID 10001 and includes no model artifacts or AWS credentials. Runtime AWS access must use the standard SDK credential chain (workload identity in EKS). The agent needs Bedrock invocation permission; the category and urgency workloads need their respective endpoint-scoped SageMaker invocation permissions. Credential provisioning for full container orchestration is a later deployment step; the documented local live path uses authorized host profiles.

Default model: `amazon.nova-lite-v1:0` in `us-east-1`, verified with a real invocation. See [LangChain's Bedrock Converse integration](https://reference.langchain.com/python/langchain-aws/chat_models/bedrock_converse/ChatBedrockConverse) and [AWS Nova Converse guidance](https://docs.aws.amazon.com/nova/latest/userguide/using-converse-api.html).

No third-party tracing is explicitly enabled; do not enable LangSmith on real tenant data without deciding what information may leave the AWS/application boundary. Demo inputs are fictional.
