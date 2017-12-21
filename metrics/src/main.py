import boto3
import os
import yaml
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
    log.debug('Config: {0}'.format(config))
    return config


def get_file_content_from_s3(bucket, key):
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket, key)
    response = obj.get()
    contents = response['Body'].read()
    return contents


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
    arn = context.invoked_function_arn
    config = setup(arn)
    publish_custom_metrics(config['custom_metrics'])
