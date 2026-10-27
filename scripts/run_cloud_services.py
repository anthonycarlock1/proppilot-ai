"""Run localhost demo APIs. Shared draft token lives only in process memory."""
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
base = {**os.environ, 'AWS_REGION': 'us-east-1', 'ASSESSMENT_WRITE_TOKEN': secrets.token_urlsafe(32)}
services = [
    ('.venv', 'services.category.app:app', 8003, {'MODEL_PROVIDER': 'sagemaker', 'CATEGORY_SAGEMAKER_ENDPOINT': 'anthony-proppilot-category-v010'}),
    ('.venv', 'services.urgency.app:app', 8005, {'MODEL_PROVIDER': 'sagemaker', 'URGENCY_SAGEMAKER_ENDPOINT': 'anthony-proppilot-urgency-v010'}),
    ('.venv', 'services.tickets.app:app', 8006, {'TICKETS_TABLE': 'anthony-proppilot-tickets'}),
    ('.venv-agent', 'services.agent.app:app', 8000, {'CATEGORY_SERVICE_URL': 'http://127.0.0.1:8003', 'URGENCY_SERVICE_URL': 'http://127.0.0.1:8005', 'TICKETS_SERVICE_URL': 'http://127.0.0.1:8006'}),
]
processes = []


def stop(*_):
    raise KeyboardInterrupt


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, stop)
    try:
        for environment, module, port, config in services:
            processes.append(subprocess.Popen([str(ROOT / environment / 'bin/python'), '-m', 'uvicorn', module,
                '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env={**base, **config}))
        print('PropPilot local APIs started; AWS profile inherited. Draft token stays in memory.', flush=True)
        while True:
            if any(process.poll() is not None for process in processes):
                raise RuntimeError('An API exited; check logs and whether ports are already in use')
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
