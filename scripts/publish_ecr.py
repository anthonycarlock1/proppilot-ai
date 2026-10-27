"""Build the checked-out application for EKS and publish immutable ECR release tags."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = '388691194728.dkr.ecr.us-east-1.amazonaws.com'
SERVICES = ('category', 'urgency', 'tickets', 'agent', 'frontend')


def main():
    account = json.loads(subprocess.check_output(['aws', 'sts', 'get-caller-identity'], text=True))['Account']
    if account != '388691194728':
        raise RuntimeError('Wrong AWS account')
    dirty = subprocess.check_output(['git', 'status', '--porcelain', '--', 'services', 'ml', 'frontend', '.dockerignore'], cwd=ROOT, text=True)
    if dirty:
        raise RuntimeError('Commit application/image source changes before publishing')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    password = subprocess.check_output(['aws', 'ecr', 'get-login-password', '--region', 'us-east-1'], text=True)
    subprocess.run(['docker', 'login', '--username', 'AWS', '--password-stdin', REGISTRY], input=password, text=True, check=True, capture_output=True)
    images = []
    for service in SERVICES:
        repository = f'anthony-proppilot-{service}'
        tag = f'eks-{revision}'
        uri = f'{REGISTRY}/{repository}:{tag}'
        # Immutable tags make reruns safe: reuse the existing release instead of overwriting it.
        existing = json.loads(subprocess.check_output(['aws', 'ecr', 'list-images', '--repository-name', repository,
            '--region', 'us-east-1', '--filter', 'tagStatus=TAGGED'], text=True))['imageIds']
        if not any(i.get('imageTag') == tag for i in existing):
            dockerfile = 'frontend/Dockerfile' if service == 'frontend' else f'services/{service}/Dockerfile'
            subprocess.run(['docker', 'build', '--platform', 'linux/amd64', '-f', dockerfile,
                '--label', f'org.opencontainers.image.revision={revision}',
                '--label', 'org.opencontainers.image.source=https://github.com/anthonycarlock1/proppilot-ai',
                '-t', uri, '.'], cwd=ROOT, check=True)
            subprocess.run(['docker', 'push', uri], check=True)
        detail = json.loads(subprocess.check_output(['aws', 'ecr', 'describe-images', '--region', 'us-east-1',
            '--repository-name', repository, '--image-ids', f'imageTag={tag}'], text=True))['imageDetails'][0]
        images.append({'service': service, 'repository': f'{REGISTRY}/{repository}', 'digest': detail['imageDigest'], 'tag': tag, 'revision': revision})
    (ROOT / 'docs/eks-images.json').write_text(json.dumps(images, indent=2) + '\n')
    manifest = ROOT / 'k8s/kustomization.yaml'
    base = manifest.read_text().split('\nimages:')[0]
    manifest.write_text(base.rstrip() + '\nimages:\n' + ''.join(
        f"  - name: proppilot/{i['service']}\n    newName: {i['repository']}\n    digest: {i['digest']}\n" for i in images))
    print('ECR publication complete; Kubernetes images pinned to recorded digests.')


if __name__ == '__main__':
    main()
