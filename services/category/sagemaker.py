"""Bounded SageMaker invocation; no fallback to a local prediction."""
import json

import boto3
from botocore.config import Config


class SageMakerPredictor:
    def __init__(self, endpoint, region, client=None):
        self.endpoint = endpoint
        self.region = region
        self._client = client

    def configured(self):
        return bool(self.endpoint and self.region)

    def predict(self, text):
        if not self.configured():
            raise ValueError('Missing SageMaker configuration')
        if self._client is None:
            self._client = boto3.client('sagemaker-runtime', region_name=self.region,
                config=Config(connect_timeout=3, read_timeout=70,
                              retries={'total_max_attempts': 1}))
        response = self._client.invoke_endpoint(EndpointName=self.endpoint,
            ContentType='application/json', Accept='application/json',
            Body=json.dumps({'text': text}).encode())
        stream = response['Body']
        try:
            return json.loads(stream.read())
        finally:
            stream.close()
