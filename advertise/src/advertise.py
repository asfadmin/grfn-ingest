from logging import getLogger
from urlparse import urljoin
import requests


log = getLogger()


def get_session(cmr_client_id):
    session = requests.Session()
    headers = {'Client-Id': cmr_client_id, 'Accept': 'application/json'}
    session.headers.update(headers)
    return session


def get_cmr_metadata(granule_concept_id, concept_search_url, session):
    url = urljoin(concept_search_url, granule_concept_id)
    response = session.get(url)
    response.raise_for_status()
    return response.text


def process_task(task_input, config, session, sns):
    log.info(task_input)
    message = get_cmr_metadata(task_input['granule_concept_id'], config['concept_search_url'], session)
    response = sns.publish(TopicArn=config['topic_arn'], Message=message)
    return {'message_id': response['MessageId']}
