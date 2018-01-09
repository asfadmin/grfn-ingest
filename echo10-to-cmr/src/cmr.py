# Report granule .echo10 xml files stored in AWS S3 to the Common Metadata Repository (CMR) via their web API
# https://wiki.earthdata.nasa.gov/display/CMR/CMR+Data+Partner+User+Guide
# https://cmr.earthdata.nasa.gov/ingest/site/ingest_api_docs.html#create-update-granule

import boto3
import requests
from logging import getLogger
from xml.etree import ElementTree
from urlparse import urljoin


log = getLogger()


def send_request(session, base_url, echo10_content):
    granule_native_id = get_granule_native_id(echo10_content)
    url = urljoin(base_url, granule_native_id)
    response = session.put(url, data=echo10_content)
    log.info('Response text: {0}'.format(response.text))
    return response


def get_session(config, s3):
    token = get_cached_token(config, s3)
    session = requests.Session()
    headers = {'Content-Type': 'application/echo10+xml', 'Echo-Token': token}
    session.headers.update(headers)
    return session


def get_file_content_from_s3(bucket, key, s3):
    obj = s3.Object(bucket, key)
    response = obj.get()
    contents = response['Body'].read()
    return contents


def get_cached_token(config, s3):
    try:
        return get_file_content_from_s3(config['bucket'], config['key'], s3)
    except Exception as e:
        return None


def get_granule_native_id(echo10_content):
    xml_element_tree = ElementTree.fromstring(echo10_content)
    granule_name = xml_element_tree.find('GranuleUR').text
    return granule_name


def push_echo10_granule_to_cmr(session, echo10_content, config, s3):
    response = send_request(session, config['granule_url'], echo10_content)
    if response.status_code == 401:
        lamb = boto3.client('lambda')
        lamb.invoke(FunctionName=config['cmr_token_lambda'])
        token = get_cached_token(config['cached_token'], s3)
        session.headers.update({'Echo-Token': token})
        response = send_request(session, config['granule_url'], echo10_content)
    response.raise_for_status()
    return response


def process_task(task_input, config, session, s3):
    log.info(task_input)
    echo10_content = get_file_content_from_s3(task_input['bucket'], task_input['key'], s3)
    response = push_echo10_granule_to_cmr(session, echo10_content, config, s3)
    return {'status': response.status_code, 'text': response.text}
