# Complete Docker Compose environments

Five application services run together: React/nginx, agent, category, urgency, and tickets. Docker DNS connects them; only nginx and prediction/debug ports are published on localhost. The ticket service has no published port. Agent debug API is at http://127.0.0.1:8004; browser API requests go through nginx at http://127.0.0.1:8080/api/.

## Start

Authenticate an authorized AWS profile, then run from the repository root:

```bash
# Development: locally trained models; real Bedrock and DynamoDB.
.venv/bin/python scripts/compose_up.py

# Staging: real Bedrock, both existing SageMaker endpoints, and DynamoDB.
.venv/bin/python scripts/compose_up.py --staging
```

The existing `.venv` contains boto3. A new checkout must first install the documented Python dependencies in [the ML guide](../ml/README.md). Docker builds all runtime dependencies independently. No AWS resources are created by these commands. Development and staging share the demo DynamoDB table by default; use fictional data. Override `TICKETS_TABLE` for a separately provisioned environment. These are two local configurations, not proof of a Kubernetes staging deployment.

The launcher resolves the selected AWS profile, forwards its credentials through process environment, generates a random internal draft token, and recreates all services so agent/ticket tokens agree. It does not write credentials or the token to source, `.env`, or images. Docker administrators can inspect container environments. Credentials are a snapshot: rerun the launcher after refreshing an expired AWS session. Do not publish `docker compose config` or container inspection output with credentials populated. Kubernetes will use workload identity rather than this local mechanism.

Health-based dependencies gate startup. Container health checks establish process liveness; readiness/cloud access must be verified separately. Model readiness only validates endpoint configuration; a successful prediction establishes remote connectivity.

## Verify and stop

```bash
docker compose ps
curl --fail http://127.0.0.1:8080/health
curl --fail http://127.0.0.1:8004/health
curl --fail http://127.0.0.1:8080/api/tickets
```

Use the assistant to assess a fictional request, review and explicitly confirm a ticket, refresh, start work, and resolve it. Ticket writes use real DynamoDB in either configuration. See [ticket verification](../services/tickets/README.md) and [browser tests](../frontend/README.md).

```bash
docker compose -f compose.yaml -f compose.staging.yaml down
```

Stopping containers preserves DynamoDB records and both SageMaker endpoints. Terraform teardown remains a separate, reviewed operation. The earlier native API launcher remains useful for debugging, but is no longer needed for this container workflow.
