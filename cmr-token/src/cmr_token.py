import base64
import json
import os
from logging import getLogger

import boto3
import requests_pkcs12

log = getLogger()
log.setLevel('INFO')
s3 = boto3.client('s3')
secrets_manager = boto3.client('secretsmanager')


def get_secret_value(secret_arn: str) -> dict:
    response = secrets_manager.get_secret_value(SecretId=secret_arn)
    return json.loads(response['SecretString'])


def get_new_token(certificate: bytes, passphrase: str) -> str:
    response = requests_pkcs12.get(
        'https://api.launchpad.nasa.gov/icam/api/sm/v1/gettoken',
        pkcs12_data=certificate,
        pkcs12_password=passphrase,
    )
    log.info('Response text: %s', response.text)
    response.raise_for_status()
    return response.json()['sm_token']


def lambda_handler(event, context):
    secret = get_secret_value(os.environ['CERTIFICATE_SECRET_ARN'])
    certificate = base64.b64decode(secret['certificate'])
    passphrase = secret['passphrase']

    token = get_new_token(certificate, passphrase)
    s3.put_object(Bucket=os.environ['BUCKET'], Key=os.environ['KEY'], Body=token)
