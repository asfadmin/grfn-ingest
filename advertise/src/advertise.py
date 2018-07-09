import boto3
import requests
from logging import getLogger
from urlparse import urljoin


log = getLogger()


def get_session(cmr_client_id):
    session = requests.Session()
    headers = {'Client-Id': cmr_client_id, 'Accept': 'application/json'}
    session.headers.update(headers)
    return session


def process_task(task_input, config, session):
    log.info(task_input)
    return {'status': 'implement me'}
