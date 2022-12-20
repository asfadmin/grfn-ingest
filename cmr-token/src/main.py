import json
from logging import getLogger
from os import getenv
from tempfile import NamedTemporaryFile

import boto3
import requests

log = getLogger()
log.setLevel('INFO')
s3 = boto3.client('s3')
CONFIG = json.loads(getenv('CONFIG'))


def get_new_token(config):
    headers = {'Content-Type': 'application/xml', 'Accept': 'application/json'}
    content = '<token><username>{0}</username><password>{1}</password><client_id>{2}</client_id>' \
              '<user_ip_address>{3}</user_ip_address><provider>{4}</provider></token>'
    content = content.format(
        config['username'], config['password'], config['client_id'], config['user_ip_address'], config['provider']
    )
    response = requests.post(config['url'], headers=headers, data=content)
    log.info('Response text: %s', response.text)
    response.raise_for_status()
    json_response = json.loads(response.text)
    return json_response['token']['id']


def cache_token(token, config):
    with NamedTemporaryFile('w') as temp:
        temp.write(token)
        temp.flush()
        s3.upload_file(temp.name, config['bucket'], config['key'])


def lambda_handler(event, context):
    token = get_new_token(CONFIG['new_token'])
    cache_token(token, CONFIG['cached_token'])
