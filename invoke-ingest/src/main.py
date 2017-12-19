import boto3
import yaml
import os
import json
from logging import getLogger


log = getLogger()


def get_maturity(arn):
    arn_tail = arn.split(':')[-1]
    if arn_tail in ['DEV', 'TEST', 'PROD']:
        maturity = arn_tail
    else:
        maturity = 'LATEST'
    return maturity


def get_config(maturity):
    config_contents = get_file_content_from_s3(os.environ['CONFIG_BUCKET'], os.environ[maturity])
    return yaml.load(config_contents)


def setup(arn):
    maturity = get_maturity(arn)
    config = get_config(maturity)
    log.setLevel(config['log_level'])
    log.info('Maturity: %s', maturity)
    log.debug('Config: %s', config)
    return config


def get_file_content_from_s3(bucket, key):
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket, key)
    response = obj.get()
    contents = response['Body'].read()
    return contents


def validate_message(message, message_error_key):
    log.debug(message)
    try:
        json.loads(message)
    except ValueError as e:
        log.warning(e.message)
        response = {message_error_key: e.message}
        return json.dumps(response)
    return message


def process_sqs_message(sfn_client, config, sqs_message):
    sns_message = json.loads(sqs_message.body)
    validated_message =  validate_message(sns_message['Message'], config['message_error_key'])
    response = sfn_client.start_execution(stateMachineArn=config['step_function_arn'], input=validated_message)
    log.info('Execution started: %s ', response['executionArn'])


def invoke_ingest(config):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName=config['queue_name'])
    sfn = boto3.client('stepfunctions')
    messages_processed = 0

    while True:
        if messages_processed >= config['max_messages_to_process']:
            log.warning('Processed %s of %s messages.  Exiting.', messages_processed, config['max_messages_to_process'])
            break

        messages = queue.receive_messages(MaxNumberOfMessages=config['max_messages_per_receive'], WaitTimeSeconds=config['wait_time_in_seconds'])
        if not messages:
            log.info('No messages found.  Exiting.')
            break

        for sqs_message in messages:
            process_sqs_message(sfn, config['message'], sqs_message)
            sqs_message.delete()
            messages_processed += 1


def lambda_handler(event, context):
    arn = context.invoked_function_arn
    config = setup(arn)
    invoke_ingest(config['invoke'])
