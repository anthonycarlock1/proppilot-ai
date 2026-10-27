# PropPilot maintenance workspace

React + TypeScript dashboard, based on Anthony's supplied visual reference: navy sidebar, light workspace, residential photo header, blue actions, summary cards, request table, and a circular breakdown chart.

The assistant drawer calls the existing chat API. Completed responses populate session activity, category counts, and recommended priorities. Reviewed assessments can be explicitly confirmed as durable tickets, listed and updated through the Tickets section. The assistant shows the model urgency separately from any confirmed-hazard escalation; users can explicitly select confirmed hazards before submitting. There are no seeded tickets, invented trends, or calibrated-confidence claims. Ticket tracking uses real DynamoDB records; active counts cover loaded ticket pages. Request/chat history is held in React memory and clears on refresh, while confirmed tickets persist; each request is independently assessed by the stateless agent.

## Local Docker preview

From the repository root, run `.venv/bin/python scripts/compose_up.py --staging` with an authorized AWS profile. All five services run in Docker, and nginx forwards `/api/` to `agent:8000` on the internal network. Open http://127.0.0.1:8080. See [complete Compose setup](../docs/compose.md) for development mode, credentials, health checks and shutdown.

The standalone frontend image still defaults to `host.docker.internal:8000` for native API debugging. Compose overrides that upstream. Vite development can use the native launcher or set `AGENT_PROXY_TARGET=http://127.0.0.1:8004` for the containerized agent. Proxy requests have a 240-second read timeout for the bounded assessment workflow.

## Frontend development

```bash
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies to `http://127.0.0.1:8000`; override with `AGENT_PROXY_TARGET` if needed. No AWS secret belongs in a `VITE_` environment variable or browser bundle.

## Verification

```bash
npm run build
npx playwright test
```

Browser tests require a running frontend and Chrome. The default executable is the locally installed macOS Google Chrome; set `CHROME_PATH` for another compatible installation. Set `FRONTEND_URL=http://127.0.0.1:8080` to test the built container instead of Vite.

Six tests use intercepted HTTP responses for deterministic success, failure, search/filter, and mobile behavior. Their results are software checks, not AWS evidence. One separate live test is opt-in:

```bash
FRONTEND_URL=http://127.0.0.1:8080 PROPPILOT_LIVE_TEST=1 npx playwright test
```

It makes paid AWS calls through the running backends, requires both actual returned model providers to be `sagemaker`, explicitly creates one fictional ticket, reloads it, starts/resolves it, and saves `docs/frontend-verification.json`. The resolved QA record is retained. Browser screenshots under `test-results/` are ignored. The baseline dashboard screenshot in `docs/frontend-dashboard.png` shows the empty state, not seeded activity.

## Source map

- `src/main.tsx`: dashboard state, derived counts, activity filters, assistant drawer, input recovery and accessibility behavior.
- `src/api.ts`: same-origin request, cancellation timeout, and readable errors.
- `src/styles.css`: responsive layout, reference-inspired styling, reduced-motion handling.
- `vite.config.ts`: local API proxy.
- `nginx.conf`: container runtime API proxy and static-file serving.

Chat responses are rendered as plain React text, not injected HTML. Urgency assessment is implemented and always requires manual review. DynamoDB ticket persistence and explicit confirmed writes are implemented. Authentication and tenant separation remain pending; use fictional data in this shared local demo.
