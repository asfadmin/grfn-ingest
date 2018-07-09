import boto3
import requests
from logging import getLogger
from urlparse import urljoin


log = getLogger()


def get_session(app_name):
    session = requests.Session()
    headers = {'app-name': app_name}
    session.headers.update(headers)
    return session


def process_task(task_input, config, session, s3):
    log.info(task_input)
    return {'status': 'implement me'}

