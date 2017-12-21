import boto3
import json
from os import environ
from logging import getLogger


log = getLogger()


def setup():
    config = json.loads(environ['CONFIG'])
    log.setLevel(config['log_level'])
    log.debug('Config: {0}'.format(config))
    return config


def get_IngestsRunning(step_function_arn):
    IngestsRunning = 0
    sfn = boto3.client('stepfunctions')

    response = sfn.list_executions(stateMachineArn=step_function_arn, statusFilter='RUNNING', maxResults=1000)
    IngestsRunning += len(response['executions'])

    while 'nextToken' in response:
        response = sfn.list_executions(stateMachineArn=step_function_arn, statusFilter='RUNNING', maxResults=1000, nextToken=response['nextToken'])
        IngestsRunning += len(response['executions'])

    return IngestsRunning


def publish_metrics(metrics):
    cloudwatch = boto3.client('cloudwatch')
    cloudwatch.put_metric_data(**metrics)


def publish_custom_metrics(config):
    metric_values = {
        'IngestsRunning': get_IngestsRunning(config['step_function_arn']),
    }

    log.info(str(metric_values))

    for metric in config['cloudwatch_metrics']['MetricData']:
        if metric['MetricName'] in metric_values:
            metric['Value'] = metric_values[metric['MetricName']]

    publish_metrics(config['cloudwatch_metrics'])


def lambda_handler(event, context):
    config = setup()
    publish_custom_metrics(config['custom_metrics'])
