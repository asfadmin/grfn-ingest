import copy
import json
import os
import pathlib
from datetime import datetime
from logging import getLogger

import boto3
from jinja2 import Template
from shapely.geometry import Polygon


log = getLogger()
log.setLevel('INFO')
CONFIG = json.loads(os.getenv('CONFIG'))

TEMPLATE_FILE = pathlib.Path(__file__).resolve().parent / 'echo10.template'

s3 = boto3.resource('s3')


def now():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def get_file_content_from_s3(bucket, key):
    obj = s3.Object(bucket, key)
    response = obj.get()
    contents = response['Body'].read()
    return contents


def write_to_file(file_name, content):
    with open(file_name, 'w') as f:
        f.write(content)


def upload_file_to_s3(local_file, bucket, key, content_type='application/xml'):
    s3.meta.client.upload_file(local_file, bucket, key, ExtraArgs={'ContentType': content_type})


def upload_content_to_s3(s3_object, content):
    local_file = os.path.join('/tmp', s3_object['key'])
    write_to_file(local_file, content)
    upload_file_to_s3(local_file, s3_object['bucket'], s3_object['key'])


def get_s3_file_size(obj):
    obj = s3.Object(obj['Bucket'], obj['Key'])
    return obj.content_length


def get_sds_metadata(obj):
    content = get_file_content_from_s3(obj['Bucket'], obj['Key'])
    sds_metadata = json.loads(content)
    return sds_metadata


def render_granule_data_as_echo10(data):
    with open(TEMPLATE_FILE, 'r') as t:
        template_text = t.read()
    template = Template(template_text)
    return template.render(data)


def render_granule_metadata(sds_metadata, config):
    granule_ur = sds_metadata['label']
    download_url = config['granule_data']['download_path'].strip
    browse_url = config['browse_path'].format(input['Browse']['Key'])
    polygon = sds_metadata['location']['coordinates'][0][:-1]

    data = {
        'granule_ur': granule_ur,
        'data_url': f'{download_url}/{granule_ur}.nc',
        'vis_url': f'{browse_url}/{granule_ur}.png',
        "sensing_start": sds_metadata['metadata']['sensing_start'],
        "sensing_stop": sds_metadata['metadata']['sensing_stop'],
        "polygon": polygon,
        "creation_timestamp": sds_metadata['creation_timestamp'],
        "upload_timestamp": now()
    }

    return render_granule_data_as_echo10(data)


def create_granule_echo10_in_s3(input, config):
    log.info('Creating echo10 file for %s', input['Product']['Key'])
    sds_metadata = get_sds_metadata(input['Metadata'])
    umm_json = render_granule_metadata(sds_metadata, config)
    output_location = {
        'bucket': config['output_bucket'],
        'key': umm_json['GranuleUR'] + '.umm_json',
    }
    upload_content_to_s3(output_location, json.dumps(umm_json))

    return output_location


def lambda_handler(event, context):
    output = create_granule_echo10_in_s3(event, CONFIG)
    return output
