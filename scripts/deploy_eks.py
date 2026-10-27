"""Deploy only the PropPilot namespace to the existing assessment cluster."""
import json
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CONTEXT = 'arn:aws:eks:us-east-1:388691194728:cluster/anthony-assessment4-eks'


def main():
    current = subprocess.check_output(['kubectl', 'config', 'current-context'], text=True).strip()
    if current != CONTEXT:
        raise RuntimeError('Select the documented Anthony assessment EKS context first')
    kubectl = ['kubectl', '--context', CONTEXT]
    manifest = (ROOT / 'k8s/kustomization.yaml').read_text()
    if 'digest: sha256:' not in manifest:
        raise RuntimeError('Publish images and pin digests before deploying')
    subprocess.run(kubectl + ['apply', '-f', str(ROOT / 'k8s/namespace.yaml')], check=True)
    found = subprocess.run(kubectl + ['-n', 'proppilot', 'get', 'secret', 'assessment-handoff', '-o', 'name'], capture_output=True, text=True)
    if found.returncode:
        # Only create after an explicit NotFound; never rotate on permission/network failures.
        if 'NotFound' not in found.stderr:
            raise RuntimeError('Cannot check assessment secret; refusing to rotate it')
        secret = {'apiVersion': 'v1', 'kind': 'Secret', 'metadata': {'name': 'assessment-handoff', 'namespace': 'proppilot'},
                  'type': 'Opaque', 'stringData': {'token': secrets.token_urlsafe(32)}}
        subprocess.run(kubectl + ['create', '-f', '-'], input=json.dumps(secret), text=True, check=True)
    subprocess.run(kubectl + ['apply', '--dry-run=server', '-k', str(ROOT / 'k8s')], check=True)
    subprocess.run(kubectl + ['apply', '-k', str(ROOT / 'k8s')], check=True)
    for service in ('category', 'urgency', 'tickets', 'agent', 'frontend'):
        subprocess.run(kubectl + ['-n', 'proppilot', 'rollout', 'status', f'deployment/{service}', '--timeout=240s'], check=True)
    print('Rollouts complete. Run the documented real-cloud verification through a localhost port-forward.')


if __name__ == '__main__':
    main()
