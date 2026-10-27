"""Administrator-only: append the scoped deployment role mapping without replacing existing roles."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CONTEXT = 'arn:aws:eks:us-east-1:388691194728:cluster/anthony-assessment4-eks'
ROLE = 'arn:aws:iam::388691194728:role/anthony-proppilot-github-deploy'


def main():
    if subprocess.check_output(['kubectl', 'config', 'current-context'], text=True).strip() != CONTEXT:
        raise RuntimeError('Wrong Kubernetes context')
    kubectl = ['kubectl', '--context', CONTEXT]
    subprocess.run(kubectl + ['apply', '-f', str(ROOT / 'k8s/ci-access.yaml')], check=True)
    cm = json.loads(subprocess.check_output(kubectl + ['-n', 'kube-system', 'get', 'configmap', 'aws-auth', '-o', 'json'], text=True))
    existing = cm['data']['mapRoles']
    if ROLE in existing:
        print('Deployment role already mapped; inspect existing mapping if permissions need changing.')
        return
    addition = f'- rolearn: {ROLE}\n  username: proppilot-ci\n  groups:\n  - proppilot-deployers\n'
    patch = [{'op': 'test', 'path': '/metadata/resourceVersion', 'value': cm['metadata']['resourceVersion']},
             {'op': 'test', 'path': '/data/mapRoles', 'value': existing},
             {'op': 'replace', 'path': '/data/mapRoles', 'value': existing.rstrip() + '\n' + addition}]
    subprocess.run(kubectl + ['-n', 'kube-system', 'patch', 'configmap', 'aws-auth', '--type=json', '-p', json.dumps(patch)], check=True)
    print('Scoped deployment mapping appended; existing node mappings preserved.')


if __name__ == '__main__':
    main()
