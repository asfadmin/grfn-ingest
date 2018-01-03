import boto3
import json
from os import environ
from datetime import datetime
from logging import getLogger


log = getLogger()


def setup():
    config = json.loads(environ['CONFIG'])
    log.setLevel(config['log_level'])
    log.debug('Config: {0}'.format(config))
    return config


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
        response['ErrorMessage'] =  error['Cause']

    return response


def send_message(message, topic):
    log.debug('SNS Message: %s', message)
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
        except Exception as e:
            log.exception('Failed to send message to response topic')

    log.info('Sending message to default topic %s', str(config['default_topic']))
    send_message(json.dumps(response), config['default_topic'])
    return response


def lambda_handler(event, context):
    config = setup()
    response = notify(event, config)
    return response
