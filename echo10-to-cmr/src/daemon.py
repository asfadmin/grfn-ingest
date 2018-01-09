import json
import boto3
from os import environ
from logging import getLogger
from botocore.client import Config
from botocore.exceptions import ClientError
from cmr import process_task, get_session


log = getLogger()


def setup():
    config = json.loads(environ['CONFIG'])
    log.setLevel(config['log_level'])
    log.debug('Config: {0}'.format(config))
    return config


def get_sfn_client(connect_timeout):
    config = Config(connect_timeout=connect_timeout, read_timeout=connect_timeout)
    sfn_client = boto3.client('stepfunctions', config=config)
    return sfn_client


def get_task(sfn_client, activity):
    task = sfn_client.get_activity_task(activityArn=activity['arn'], workerName=activity['worker_name'])
    return task


def send_task_response(sfn_client, token, output=None, exception=None):
    try:
        if not exception:
            sfn_client.send_task_success(taskToken=token, output=json.dumps(output))
        else:
            sfn_client.send_task_failure(taskToken=token, error=type(exception).__name__, cause=str(exception))
    except ClientError as e:
        if e.response['Error']['Code'] == 'TaskTimedOut':
            log.exception('Failed to send task response.  Task timed out.')
        else:
            raise


def daemon_loop(config, get_remaining_time_in_millis_fcn):
    log.info('Daemon started')
    session = get_session(config['cmr']['cached_token'])
    s3 = boto3.resource('s3')
    sfn_client = get_sfn_client(config['sfn_connect_timeout'])
    while True:
        if get_remaining_time_in_millis_fcn() < config['max_task_time_in_millis']:
            log.info('Remaining time %s less than max task time %s.  Exiting.', get_remaining_time_in_millis_fcn(), config['max_task_time_in_millis'])
            break

        task = get_task(sfn_client, config['activity'])
        if 'taskToken' not in task:
            log.info('No tasks found.  Exiting')
            break

        try:
            task_input = json.loads(task['input'])
            output = process_task(task_input, config['cmr'], session, s3)
            send_task_response(sfn_client, task['taskToken'], output)
        except Exception as e:
            log.exception('Failed to process task.')
            send_task_response(sfn_client, task['taskToken'], exception=e)


def lambda_handler(event, context):
    config = setup()
    daemon_loop(config['daemon'], context.get_remaining_time_in_millis)
