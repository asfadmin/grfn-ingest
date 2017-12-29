#!/usr/bin/env python3
import json
import logging
import tempfile
from argparse import ArgumentParser
from os import chdir
from shutil import rmtree

import boto3
import yaml
from boto.utils import get_instance_metadata
from botocore.client import Config
from botocore.exceptions import ClientError
from ingest import process_task


def get_instance_id():
    instance_metadata = get_instance_metadata()
    return instance_metadata['instance-id']


def get_task(activity):
    config = Config(connect_timeout=activity['timeout'], read_timeout=activity['timeout'])
    sfn = boto3.client('stepfunctions', config=config)
    task = sfn.get_activity_task(activityArn=activity['arn'], workerName=activity['worker_name'])
    return task


def get_config(config_file_name):
    with open(config_file_name, 'r') as f:
        config = yaml.load(f)
    return config


def get_s3_config_file(s3_path):
    path_parts = s3_path.split('/')
    tcf = tempfile.NamedTemporaryFile()

    s3_client = boto3.client('s3')
    s3_client.download_file(path_parts[2], '/'.join(path_parts[3:]), tcf.name)
    config = get_config(tcf.name)

    tcf.close()
    return config


def get_command_line_options():
    parser = ArgumentParser('Ingest Sentinel-1 interferogram products')
    parser.add_argument(
        '-c', '--config',
        action='store',
        dest='config_file',
        default='../ingest_config.yaml',
        help='use a specific config file, local path or S3 URI',
    )
    options = parser.parse_args()
    return options


def get_logger():
    log = logging.getLogger()
    stdout_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s: %(message)s (%(filename)s line %(lineno)d)')
    stdout_handler.setFormatter(formatter)
    log.addHandler(stdout_handler)
    return log


def adjust_log_levels(log_config):
    log.setLevel(log_config['base_level'])
    logging.getLogger('botocore').setLevel(log_config['boto_level'])
    logging.getLogger('boto3').setLevel(log_config['boto_level'])


def send_task_response(token, output=None, exception=None):
    sfn = boto3.client('stepfunctions')
    try:
        if not exception:
            sfn.send_task_success(taskToken=token, output=json.dumps(output))
        else:
            sfn.send_task_failure(taskToken=token, error=type(exception).__name__, cause=str(exception))
    except ClientError as e:
        if e.response['Error']['Code'] == 'TaskTimedOut':
            log.exception('Failed to send task response.  Task timed out.')
        else:
            raise


def setup_working_directory():
    working_directory = tempfile.mkdtemp()
    chdir(working_directory)
    return working_directory


def daemon_loop(config):
    log.info('Ingest daemon started')
    while True:
        task = get_task(config['activity'])
        if 'taskToken' in task:
            try:
                working_directory = setup_working_directory()
                task_input = json.loads(task['input'])
                output = process_task(task_input, config['ingest'])
                send_task_response(task['taskToken'], output)
            except Exception as e:
                log.exception('Failed to process task.')
                send_task_response(task['taskToken'], exception=e)
            finally:
                rmtree(working_directory)


def setup():
    options = get_command_line_options()
    if options.config_file.startswith('s3://'):
        config = get_s3_config_file(options.config_file)
    else:
        config = get_config(options.config_file)
    adjust_log_levels(config['log'])
    boto3.setup_default_session(region_name=config['aws_region'])
    if config['daemon']['activity']['worker_name'] == '$INSTANCE_ID':
        config['daemon']['activity']['worker_name'] = get_instance_id()
    return config


log = get_logger()

if __name__ == "__main__":
    config = setup()
    daemon_loop(config['daemon'])
