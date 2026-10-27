"""Copy the verified GHCR release into ECR and update the Kubernetes digest pins."""
import json
import os
from pathlib import Path
import subprocess

REGISTRY = '388691194728.dkr.ecr.us-east-1.amazonaws.com'
ROOT = Path(__file__).resolve().parents[1]


def main():
    revision = os.environ['GITHUB_SHA']
    release = json.loads((ROOT / 'release-images.json').read_text())
    if set(release) != {'category', 'urgency', 'agent', 'tickets', 'frontend'}:
        raise RuntimeError('Expected a complete five-image release')
    identity = json.loads(subprocess.check_output(['aws', 'sts', 'get-caller-identity'], text=True))
    if identity['Account'] != '388691194728':
        raise RuntimeError('Wrong AWS account')
    password = subprocess.check_output(['aws', 'ecr', 'get-login-password', '--region', 'us-east-1'], text=True)
    subprocess.run(['docker', 'login', '--username', 'AWS', '--password-stdin', REGISTRY],
                   input=password, text=True, check=True, capture_output=True)
    images = []
    for service, source in release.items():
        if source['revision'] != revision:
            raise RuntimeError('Release source revision mismatch')
        repository = f'anthony-proppilot-{service}'
        tag = f'ci-{revision}'
        uri = f'{REGISTRY}/{repository}:{tag}'
        # A failed DescribeImages is not evidence that a tag is missing.
        described = subprocess.run(['aws', 'ecr', 'describe-images', '--region', 'us-east-1',
            '--repository-name', repository, '--image-ids', f'imageTag={tag}'], capture_output=True, text=True)
        if described.returncode:
            if 'ImageNotFoundException' not in described.stderr:
                raise RuntimeError(f'Cannot check ECR release for {service}')
            subprocess.run(['docker', 'tag', source['digest'], uri], check=True)
            subprocess.run(['docker', 'push', uri], check=True)
            described = subprocess.run(['aws', 'ecr', 'describe-images', '--region', 'us-east-1',
                '--repository-name', repository, '--image-ids', f'imageTag={tag}'], capture_output=True, text=True, check=True)
        detail = json.loads(described.stdout)['imageDetails'][0]
        digest = detail['imageDigest']
        # Docker push can change an index to a platform manifest. Verify the pulled runtime image ID instead.
        subprocess.run(['docker', 'pull', f'{REGISTRY}/{repository}@{digest}'], check=True)
        def image_id(name):
            return subprocess.check_output(['docker', 'image', 'inspect', name, '--format', '{{.Id}}'], text=True).strip()
        if image_id(source['digest']) != image_id(f'{REGISTRY}/{repository}@{digest}'):
            raise RuntimeError(f'ECR runtime image differs from verified GHCR source: {service}')
        images.append({'service': service, 'source': source['digest'], 'repository': f'{REGISTRY}/{repository}',
                       'digest': digest, 'revision': revision, 'runtime_image_id_preserved': True})
    manifest = ROOT / 'k8s/base/kustomization.yaml'
    manifest.write_text(manifest.read_text().split('\nimages:')[0].rstrip() + '\nimages:\n' + ''.join(
        f"  - name: proppilot/{i['service']}\n    newName: {i['repository']}\n    digest: {i['digest']}\n" for i in images))
    (ROOT / 'release-ecr-images.json').write_text(json.dumps(images, indent=2) + '\n')
    print('ECR runtime image IDs match the verified GHCR release; Kubernetes digests updated.')


if __name__ == '__main__':
    main()
