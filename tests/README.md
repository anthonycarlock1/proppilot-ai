# Running tests

From the project root, after training the local category model and installing the documented dependencies:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_category.py' -v
.venv/bin/python -m unittest discover -s tests -p 'test_sagemaker.py' -v
.venv/bin/python -m unittest discover -s tests -p 'test_urgency.py' -v
.venv/bin/python -m unittest discover -s tests -p 'test_tickets.py' -v
.venv-agent/bin/python -m unittest discover -s tests -p 'test_agent.py' -v
```

The environments are intentionally separate. The ML environment does not need LangChain; the agent environment does not need scikit-learn. Agent tests inject scripted model messages and a fake prediction function, so they make no AWS calls.

Cloud integration is checked separately by `scripts/verify_sagemaker_category.py` (ML environment) and `scripts/verify_chat.py` (standard library, running HTTP services required). Those checks make paid AWS requests and save dated evidence. A saved verification file is historical evidence, not a live health check.

Frontend browser checks run from `frontend/` with `npx playwright test`. Use `FRONTEND_URL=http://127.0.0.1:8080` for the Docker-served UI. Six tests intercept API responses; the separate live test requires `PROPPILOT_LIVE_TEST=1` and running authorized backends. It asserts both model providers are SageMaker, creates one fictional reviewed ticket, reloads it, starts/resolves it, and verifies persisted version 3. See `frontend/README.md` for browser setup and evidence details. Run `.venv/bin/python scripts/verify_sagemaker_urgency.py` for urgency inference/policy checks. After `verify_chat.py` saves a real draft, `.venv/bin/python scripts/verify_tickets.py` tests real DynamoDB concurrency and retains its own fictional resolved QA ticket.
