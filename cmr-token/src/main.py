import boto3
import requests
import json
from os import getenv
from logging import getLogger
from tempfile import NamedTemporaryFile


log = getLogger()
s3 = boto3.client('s3')


def setup():
    log.setLevel('INFO')
    config = json.loads(getenv('CONFIG'))
    return config


def get_new_token(config):
    headers = {'Content-Type': 'application/xml', 'Accept': 'application/json'}
    content = '<token><username>{0}</username><password>{1}</password><client_id>{2}</client_id><user_ip_address>{3}</user_ip_address><provider>{4}</provider></token>'.format(
        config['username'], config['password'], config['client_id'], config['user_ip_address'], config['provider']
    )
    response = requests.post(config['url'], headers=headers, data=content)
    log.info('Response text: {0}'.format(response.text))
    response.raise_for_status()
    json_response = json.loads(response.text)
    return json_response['token']['id']


def cache_token(token, config):
    with NamedTemporaryFile() as temp:
        temp.write(token)
        temp.flush()
        s3.upload_file(temp.name, config['bucket'], config['key'])


def lambda_handler(event, context):
    config = setup()
    token = get_new_token(config['new_token'])
    cache_token(token, config['cached_token'])
