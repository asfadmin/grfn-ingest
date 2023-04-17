import json
from logging import getLogger
from os import getenv

import boto3


log = getLogger()
log.setLevel('INFO')
CONFIG = json.loads(getenv('CONFIG'))

sqs = boto3.resource('sqs')
sfn = boto3.client('stepfunctions')


def validate_message(message, message_error_key):
    try:
        json.loads(message)
    except ValueError as e:
        log.warning(e)
        response = {message_error_key: str(e)}
        return json.dumps(response)
    return message


def process_sqs_message(sfn_client, config, sqs_message):
    sns_message = json.loads(sqs_message.body)
    validated_message = validate_message(sns_message['Message'], config['message_error_key'])
    response = sfn_client.start_execution(stateMachineArn=config['step_function_arn'], input=validated_message)
    log.info('Execution started: %s ', response['executionArn'])


def invoke_ingest(config):
    queue = sqs.Queue(config['queue_url'])
    messages_processed = 0

    while True:
        if messages_processed >= config['max_messages_to_process']:
            log.warning('Processed %s of %s messages.  Exiting.', messages_processed, config['max_messages_to_process'])
            break

        messages = queue.receive_messages(MaxNumberOfMessages=config['max_messages_per_receive'],
                                          WaitTimeSeconds=config['wait_time_in_seconds'])
        if not messages:
            log.info('No messages found.  Exiting.')
            break

        for sqs_message in messages:
            process_sqs_message(sfn, config['message'], sqs_message)
            sqs_message.delete()
            messages_processed += 1


def lambda_handler(event, context):
    invoke_ingest(CONFIG)
