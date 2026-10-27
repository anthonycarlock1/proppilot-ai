"""Start the complete demo without writing AWS credentials or the draft token to disk."""
import argparse
import os
from pathlib import Path
import secrets
import subprocess

import boto3

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staging', action='store_true', help='Use both real SageMaker endpoints')
    args = parser.parse_args()
    credentials = boto3.Session().get_credentials()
    if credentials is None:
        parser.error('No AWS credentials found. Authenticate your authorized AWS profile first.')
    frozen = credentials.get_frozen_credentials()
    environment = {**os.environ,
                   'AWS_ACCESS_KEY_ID': frozen.access_key,
                   'AWS_SECRET_ACCESS_KEY': frozen.secret_key,
                   'AWS_SESSION_TOKEN': frozen.token or '',
                   'ASSESSMENT_WRITE_TOKEN': secrets.token_urlsafe(32)}
    command = ['docker', 'compose', '-f', 'compose.yaml']
    if args.staging:
        command += ['-f', 'compose.staging.yaml']
    # Recreate all services together so the agent and ticket tokens always agree.
    command += ['up', '-d', '--build', '--force-recreate', '--wait', '--wait-timeout', '180']
    subprocess.run(command, cwd=ROOT, env=environment, check=True)
    print('PropPilot is ready at http://127.0.0.1:8080. Credentials were not written to files.')
    print('Docker administrators can inspect container environments. Restart after AWS credentials expire.')


if __name__ == '__main__':
    main()
