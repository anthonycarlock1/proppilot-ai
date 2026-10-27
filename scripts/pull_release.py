"""Pull a commit-tagged GHCR release, check provenance labels, and pin Compose digests."""
import json
import os
from pathlib import Path
import re
import subprocess


def main():
    repository = os.environ['GITHUB_REPOSITORY'].lower()
    revision = os.environ['GITHUB_SHA']
    if not re.fullmatch(r'[a-f0-9]{40}', revision):
        raise ValueError('Expected a full Git commit SHA')
    if not re.fullmatch(r'[a-z0-9_.-]+/[a-z0-9_.-]+', repository):
        raise ValueError('Expected owner/repository')
    services, evidence = {}, {}
    for service in ('category', 'urgency', 'tickets', 'agent', 'frontend'):
        name = f'ghcr.io/{repository}-{service}'
        tag = f'{name}:sha-{revision}'
        subprocess.run(['docker', 'pull', tag], check=True)
        info = json.loads(subprocess.check_output(['docker', 'image', 'inspect', tag], text=True))[0]
        if info['Config']['Labels'].get('org.opencontainers.image.revision') != revision:
            raise RuntimeError(f'Image revision mismatch: {service}')
        digest = next(item for item in info['RepoDigests'] if item.startswith(name + '@sha256:'))
        services[service] = {'image': digest, 'pull_policy': 'never'}
        evidence[service] = {'tag': tag, 'digest': digest, 'revision': revision}
    Path('compose.release.json').write_text(json.dumps({'services': services}, indent=2) + '\n')
    Path('release-images.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print('Published release pulled, revision labels checked, and Compose pinned to digests.')


if __name__ == '__main__':
    main()
