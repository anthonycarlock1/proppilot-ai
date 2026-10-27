"""DynamoDB records and atomic ticket creation; no in-memory storage fallback."""
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from uuid import uuid4

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.config import Config
from botocore.exceptions import ClientError

serialize = TypeSerializer()
deserialize = TypeDeserializer()


class TicketError(Exception):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def wire(item):
    return {key: serialize.serialize(value) for key, value in item.items()}


def plain(item):
    return {key: deserialize.deserialize(value) for key, value in item.items()}


def now():
    return datetime.now(timezone.utc).isoformat()


class TicketStore:
    def __init__(self, client=None, table=None):
        self.table = table or os.getenv('TICKETS_TABLE', 'anthony-proppilot-tickets')
        self._client = client

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'),
                config=Config(connect_timeout=3, read_timeout=8, retries={'total_max_attempts': 2}))
        return self._client

    def get(self, pk, sk='RECORD'):
        result = self.client.get_item(TableName=self.table, Key=wire({'pk': pk, 'sk': sk}), ConsistentRead=True)
        return plain(result['Item']) if 'Item' in result else None

    def draft(self, payload):
        identifier = str(uuid4())
        item = {'pk': f'ASSESSMENT#{identifier}', 'sk': 'RECORD', 'assessment_id': identifier,
                **payload, 'created_at': now(), 'expires_at': int(time.time()) + 86400}
        self.client.put_item(TableName=self.table, Item=wire(item), ConditionExpression='attribute_not_exists(pk)')
        return {key: value for key, value in item.items() if key not in {'pk', 'sk'}}

    def get_ticket(self, identifier):
        item = self.get('WORKSPACE#demo', f'TICKET#{identifier}')
        if item is None:
            raise TicketError(404, 'Ticket not found')
        return {key: value for key, value in item.items() if key not in {'pk', 'sk'}}

    def replay(self, key, fingerprint):
        previous = self.get(f'IDEMPOTENCY#{key}')
        if previous:
            if previous['fingerprint'] != fingerprint:
                raise TicketError(409, 'This idempotency key was used for a different request')
            return self.get_ticket(previous['ticket_id'])
        return None

    def create(self, payload, key):
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        previous = self.replay(key, fingerprint)
        if previous:
            return previous, True
        assessment_id = payload['assessment_id']
        draft = self.get(f'ASSESSMENT#{assessment_id}')
        if not draft:
            raise TicketError(404, 'Assessment not found; run a new assessment')
        if draft['expires_at'] <= int(time.time()):
            raise TicketError(410, 'Assessment expired; run a new assessment')
        if self.get(f'ASSESSMENT_TICKET#{assessment_id}'):
            raise TicketError(409, 'A ticket already exists for this assessment; refresh the ticket list')
        identifier = 'PP-' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f') + '-' + uuid4().hex[:8]
        timestamp = now()
        item = {'pk': 'WORKSPACE#demo', 'sk': f'TICKET#{identifier}', 'ticket_id': identifier,
                **payload, 'description': draft['description'], 'assessment': draft['assessment'],
                'status': 'open', 'version': 1, 'created_at': timestamp, 'updated_at': timestamp}
        records = [item,
            {'pk': f'IDEMPOTENCY#{key}', 'sk': 'RECORD', 'ticket_id': identifier, 'fingerprint': fingerprint},
            {'pk': f'ASSESSMENT_TICKET#{assessment_id}', 'sk': 'RECORD', 'ticket_id': identifier}]
        actions = [{'Put': {'TableName': self.table, 'Item': wire(record),
                            'ConditionExpression': 'attribute_not_exists(pk)'}} for record in records]
        actions.append({'ConditionCheck': {'TableName': self.table,
            'Key': wire({'pk': f'ASSESSMENT#{assessment_id}', 'sk': 'RECORD'}),
            'ConditionExpression': 'expires_at > :current', 'ExpressionAttributeValues': wire({':current': int(time.time())})}})
        try:
            self.client.transact_write_items(TransactItems=actions)
        except ClientError as exc:
            if exc.response['Error']['Code'] != 'TransactionCanceledException':
                raise
            previous = self.replay(key, fingerprint)
            if previous:
                return previous, True
            if self.get(f'ASSESSMENT_TICKET#{assessment_id}'):
                raise TicketError(409, 'A ticket already exists for this assessment; refresh the ticket list') from None
            raise TicketError(503, 'Ticket creation was interrupted; retry with the same confirmation') from None
        return {k: v for k, v in item.items() if k not in {'pk', 'sk'}}, False

    def list(self, limit=20, cursor=None):
        arguments = {'TableName': self.table, 'KeyConditionExpression': 'pk = :pk AND begins_with(sk, :prefix)',
            'ExpressionAttributeValues': wire({':pk': 'WORKSPACE#demo', ':prefix': 'TICKET#'}),
            'ScanIndexForward': False, 'ConsistentRead': True, 'Limit': limit}
        if cursor:
            arguments['ExclusiveStartKey'] = wire({'pk': 'WORKSPACE#demo', 'sk': f'TICKET#{cursor}'})
        response = self.client.query(**arguments)
        items = [{k: v for k, v in plain(item).items() if k not in {'pk', 'sk'}} for item in response.get('Items', [])]
        last = response.get('LastEvaluatedKey')
        return {'items': items, 'next_cursor': plain(last)['sk'].removeprefix('TICKET#') if last else None}

    def update(self, identifier, status, expected_version):
        current = self.get_ticket(identifier)
        if current['version'] != expected_version:
            raise TicketError(409, 'Ticket changed; refresh before updating')
        if status == current['status']:
            return current
        if (current['status'], status) not in {('open', 'in_progress'), ('in_progress', 'resolved')}:
            raise TicketError(409, 'Allowed transitions: open to in_progress to resolved')
        try:
            response = self.client.update_item(TableName=self.table,
                Key=wire({'pk': 'WORKSPACE#demo', 'sk': f'TICKET#{identifier}'}),
                UpdateExpression='SET #status = :status, #version = :next, updated_at = :time',
                ConditionExpression='#version = :expected AND #status = :previous',
                ExpressionAttributeNames={'#status': 'status', '#version': 'version'},
                ExpressionAttributeValues=wire({':status': status, ':next': expected_version + 1,
                    ':time': now(), ':expected': expected_version, ':previous': current['status']}), ReturnValues='ALL_NEW')
        except ClientError as exc:
            if exc.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise TicketError(409, 'Ticket changed; refresh before updating') from None
            raise
        return {k: v for k, v in plain(response['Attributes']).items() if k not in {'pk', 'sk'}}
