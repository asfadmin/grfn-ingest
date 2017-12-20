import boto3
import yaml
import os
import json
from datetime import datetime
from logging import getLogger


log = getLogger()


def get_maturity(arn):
    arn_tail = arn.split(':')[-1]
    if arn_tail in ['DEV', 'TEST', 'PROD']:
        maturity = arn_tail
    else:
        maturity = 'LATEST'
    return maturity


def get_file_content_from_s3(bucket, key):
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket, key)
    response = obj.get()
    contents = response['Body'].read()
    return contents


def get_config(maturity):
    config_contents = get_file_content_from_s3(os.environ['CONFIG_BUCKET'], os.environ[maturity])
    return yaml.load(config_contents)


def setup(arn):
    maturity = get_maturity(arn)
    config = get_config(maturity)
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
    arn = context.invoked_function_arn
    config = setup(arn)
    response = notify(event, config)
    return response
