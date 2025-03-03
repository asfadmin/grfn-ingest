import json
from logging import getLogger

import boto3
import botocore
import jsonschema


log = getLogger()
log.setLevel('INFO')
s3 = boto3.resource('s3')


class InvalidMessage(Exception):
    pass


class MissingFile(Exception):
    pass


class InvalidMetadata(Exception):
    pass


def get_file_content_from_s3(bucket, key):
    obj = s3.Object(bucket, key)
    response = obj.get()
    contents = response['Body'].read()
    return contents


def get_json_from_file(filename):
    with open(filename) as f:
        content = json.load(f)
    return content


def validate_s3_object(obj):
    try:
        s3.Object(obj['Bucket'], obj['Key']).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] in ['403', '404']:
            raise MissingFile(str(obj) + ' ' + str(e))
        raise


def validate_message(message):
    if 'MessageError' in message:
        raise InvalidMessage(message['MessageError'])
    message_schema = get_json_from_file('message_schema.json')
    try:
        jsonschema.validate(message, message_schema)
    except jsonschema.exceptions.ValidationError as e:
        raise InvalidMessage(e.message)


def validate_metadata(obj):
    metadata = get_file_content_from_s3(obj['Bucket'], obj['Key'])
    metadata_schema = get_json_from_file('metadata_schema.json')

    try:
        metadata = json.loads(metadata)
    except json.decoder.JSONDecodeError as e:
        raise InvalidMetadata(str(e))

    try:
        jsonschema.validate(metadata, metadata_schema)
    except jsonschema.exceptions.ValidationError as e:
        raise InvalidMetadata(e.message)


def verify(message):
    validate_message(message)

    validate_s3_object(message['Metadata'])
    validate_s3_object(message['Browse'])
    validate_s3_object(message['Product'])

    validate_metadata(message['Metadata'])


def lambda_handler(event, context):
    verify(event)
