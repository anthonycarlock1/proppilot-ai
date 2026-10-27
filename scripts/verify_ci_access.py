"""Verify the authenticated CI principal's actual Kubernetes permission boundary."""
import json
from pathlib import Path
import subprocess


def main():
    checks = [('patch', 'deployments', None, 'proppilot', True),
              ('create', 'services', None, 'proppilot', True),
              ('create', 'pods', 'portforward', 'proppilot', True),
              ('get', 'secrets', None, 'proppilot', False),
              ('create', 'serviceaccounts', None, 'proppilot', False),
              ('patch', 'configmaps', None, 'kube-system', False),
              ('patch', 'deployments', None, 'platform-team', False),
              ('create', 'namespaces', None, None, False)]
    results = []
    for verb, resource, subresource, namespace, expected in checks:
        command = ['kubectl', 'auth', 'can-i', verb, resource]
        if namespace:
            command += ['-n', namespace]
        if subresource:
            command += ['--subresource', subresource]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.stdout.strip() not in ('yes', 'no'):
            raise RuntimeError('Permission check failed to produce a valid authorization decision')
        allowed = result.stdout.strip() == 'yes'
        if allowed != expected:
            raise RuntimeError(f'Unexpected permission: {verb} {resource} in {namespace}')
        results.append({'verb': verb, 'resource': resource, 'subresource': subresource,
                        'namespace': namespace, 'allowed': allowed})
    Path('ci-access-verification.json').write_text(json.dumps({'method': 'Actual authenticated deployment principal', 'checks': results}, indent=2) + '\n')
    print('Scoped deployment access verified; Secrets and cross-namespace/cluster writes denied.')


if __name__ == '__main__':
    main()
