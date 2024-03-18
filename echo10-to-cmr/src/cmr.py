# Report granule .echo10 xml files stored in AWS S3 to the Common Metadata Repository (CMR) via their web API
# https://wiki.earthdata.nasa.gov/display/CMR/CMR+Data+Partner+User+Guide
# https://cmr.earthdata.nasa.gov/ingest/site/ingest_api_docs.html#create-update-granule

import json
from logging import getLogger
from urllib.parse import urljoin

import boto3
import requests

log = getLogger()


def send_request(session, base_url, metadata_content):
    metadata = json.loads(metadata_content)
    granule_native_id = metadata['GranuleUR']
    content_type = f'application/vnd.nasa.cmr.umm+json;version={metadata["MetadataSpecification"]["Version"]}'
    url = urljoin(base_url, granule_native_id)
    response = session.put(url, headers={'Content-Type': content_type}, data=metadata_content)
    log.info('Response text: %s', response.text)
    return response.json()


def get_session(config, s3):
    token = get_cached_token(config, s3)
    session = requests.Session()
    headers = {'Accept': 'application/json', 'Authorization': token}
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
    except Exception:
        return None


def push_granule_metadata_to_cmr(session, metadata_content, config, s3):
    response = send_request(session, config['granule_url'], metadata_content)
    if response.status_code == 401:
        lamb = boto3.client('lambda')
        lamb.invoke(FunctionName=config['cmr_token_lambda'])
        token = get_cached_token(config['cached_token'], s3)
        session.headers.update({'Authorization': token})
        response = send_request(session, config['granule_url'], metadata_content)
    response.raise_for_status()
    return response


def process_task(task_input, config, session, s3):
    log.info(task_input)
    metadata_content = get_file_content_from_s3(task_input['bucket'], task_input['key'], s3)
    response = push_granule_metadata_to_cmr(session, metadata_content, config, s3)
    return response['concept-id']
