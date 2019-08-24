import json
from logging import getLogger
import botocore
import boto3
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

class InvalidTopic(Exception):
    pass


def get_file_content_from_s3(bucket, key):
    obj = s3.Object(bucket, key)
    response = obj.get()
    contents = response['Body'].read()
    return contents


def get_json_from_file(filename):
    with open(filename, 'r') as f:
        content = f.read()
    return json.loads(content)


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
        raise InvalidMessage(str(e))


def validate_metadata(obj):
    metadata = get_file_content_from_s3(obj['Bucket'], obj['Key'])
    metadata_schema = get_json_from_file('metadata_schema.json')
    try:
        metadata = json.loads(metadata)
        jsonschema.validate(metadata, metadata_schema)
    except (ValueError, jsonschema.exceptions.ValidationError) as e:
        raise InvalidMetadata(str(e))


def json_error(error):
    json_messages = [
        'Invalid parameter: Message Structure - JSON message body failed to parse',
        'Invalid parameter: Message Structure - No default entry in JSON message body',
    ]
    return error['Code'] == 'InvalidParameter' and error['Message'] in json_messages


def validate_topic(topic):
    sns = boto3.client('sns', region_name=topic['Region'])
    try:
        sns.publish(TopicArn=topic['Arn'], Message='invalidMessage', MessageStructure='json')
    except botocore.exceptions.ClientError as e:
        if not json_error(e.response['Error']):
            raise InvalidTopic(str(e))


def verify(message):
    validate_message(message)

    if 'ResponseTopic' in message:
        validate_topic(message['ResponseTopic'])

    validate_s3_object(message['Metadata'])
    validate_s3_object(message['Browse'])
    validate_s3_object(message['Product'])

    validate_metadata(message['Metadata'])


def lambda_handler(event, context):
    verify(event)
