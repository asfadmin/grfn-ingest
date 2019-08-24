import json
from os import getenv
from datetime import datetime
from logging import getLogger
import boto3


log = getLogger()
log.setLevel('INFO')
CONFIG = json.loads(getenv('CONFIG'))


def create_response(event, error_config):
    response = {
        'ProductName': event.get('ProductName', ''),
        'DeliveryTime': event.get('DeliveryTime', ''),
        'Status': 'success',
        'IngestTime': datetime.utcnow().isoformat(),
    }

    error = event.get(error_config['key'])
    if error:
        response['Status'] = 'failure'
        if error['Error'] in error_config['codes']:
            response['ErrorCode'] = error['Error']
        else:
            response['ErrorCode'] = error_config['default_code']
        response['ErrorMessage'] = error['Cause']

    return response


def send_message(message, topic):
    client = boto3.client('sns', region_name=topic['Region'])
    response = client.publish(
        TopicArn=topic['Arn'],
        Message=message,
    )
    log.info('SNS Message Id: %s', response['MessageId'])


def notify(event, config):
    response = create_response(event, config['errors'])

    if 'ResponseTopic' in event:
        log.info('Sending message to response topic %s', str(event['ResponseTopic']))
        try:
            send_message(json.dumps(response), event['ResponseTopic'])
            return response
        except Exception:
            log.exception('Failed to send message to response topic')

    log.info('Sending message to default topic %s', str(config['default_topic']))
    send_message(json.dumps(response), config['default_topic'])
    return response


def lambda_handler(event, context):
    response = notify(event, CONFIG)
    return response
