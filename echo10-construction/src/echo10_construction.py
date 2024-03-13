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


def get_mission(polygon, missions):
    granule = Polygon(polygon)
    for mission in missions:
        aoi = Polygon(mission['coords'])
        if granule.intersects(aoi):
            return mission['name']
    return None


def get_granule_data(input, config):
    sds_metadata = get_sds_metadata(input['Metadata'])
    granule_metadata = sds_metadata['metadata']

    collection = config['collection']
    granule_ur = sds_metadata['label']
    file_size = get_s3_file_size(input['Product'])
    browse_url = config['browse_path'].format(input['Browse']['Key'])
    online_access_url = config['download_path'].format(input['Product']['Key'])
    polygon = sds_metadata['location']['coordinates'][0][:-1]
    mission = get_mission(polygon, config['missions'])

    input_granules = ['[Reference] {0}'.format(g) for g in granule_metadata['reference_scenes']]
    input_granules += ['[Secondary] {0}'.format(g) for g in granule_metadata['secondary_scenes']]

    data = {
        'granule_ur': granule_ur,
        'insert_time': now(),
        'last_update': now(),
        'collection': collection['dataset_id'],
        'size_mb_data_granule': float(file_size) / 1024 / 1024,
        'producer_granule_id': sds_metadata['label'],
        'production_date_time': sds_metadata['creation_timestamp'],
        'beginning_date_time': granule_metadata['sensing_start'],
        'ending_date_time': granule_metadata['sensing_stop'],
        'orbits': granule_metadata['orbit_number'],
        'platforms': sorted(set(p.upper() for p in granule_metadata['platform'])),
        'sensor_short_name': granule_metadata['beam_mode'],
        'polygon': polygon,
        'additional_attributes': {
            'GROUP_ID': sds_metadata['label'].replace('.', '-'),
            'ASCENDING_DESCENDING': granule_metadata['orbit_direction'],
            'BEAM_MODE_TYPE': granule_metadata['dataset_type'],
            'BEAM_MODE': granule_metadata['beam_mode'],
            'BEAM_MODE_DESC': granule_metadata['product_type'],
            'POLARIZATION': granule_metadata['polarization'],
            'LOOK_DIRECTION': granule_metadata['look_direction'],
            'PATH_NUMBER': granule_metadata['track_number'],
            'BYTES': file_size,
            'NEAR_START_LON': granule_metadata['ogr_bbox'][0][0],
            'NEAR_START_LAT': granule_metadata['ogr_bbox'][0][1],
            'FAR_START_LON': granule_metadata['ogr_bbox'][1][0],
            'FAR_START_LAT': granule_metadata['ogr_bbox'][1][1],
            'FAR_END_LON': granule_metadata['ogr_bbox'][2][0],
            'FAR_END_LAT': granule_metadata['ogr_bbox'][2][1],
            'NEAR_END_LON': granule_metadata['ogr_bbox'][3][0],
            'NEAR_END_LAT': granule_metadata['ogr_bbox'][3][1],
            'ASF_PLATFORM': 'Sentinel-1 Interferogram (BETA)',
            'PROCESSING_TYPE': collection['processing_type'],
            'PROCESSING_TYPE_DISPLAY': collection['processing_type_display'],
            'PROCESSING_DESCRIPTION': collection['processing_description'],
            'THUMBNAIL_URL': browse_url,
            'PERPENDICULAR_BASELINE': granule_metadata['perpendicular_baseline'],
            'MISSION_NAME': mission,
            'VERSION': sds_metadata['version'],
        },
        'input_granules': input_granules,
        'visible': 'true',
        'orderable': 'true',
        'online_access_url': online_access_url,
        'browse_url': browse_url,
    }

    if 'temporal_baseline_days' in granule_metadata:
        data['additional_attributes']['TEMPORAL_BASELINE_DAYS'] = granule_metadata['temporal_baseline_days']

    if 'weather_model' in granule_metadata:
        data['additional_attributes']['WEATHER_MODEL'] = granule_metadata['weather_model']

    if 'frame_number' in granule_metadata:
        data['additional_attributes']['FRAME_NUMBER'] = granule_metadata['frame_number']

    return data


def render_granule_data_as_echo10(data):
    with open(TEMPLATE_FILE, 'r') as t:
        template_text = t.read()
    template = Template(template_text)
    return template.render(data)


def create_granule_echo10_in_s3(input, config):
    log.info('Creating echo10 file for %s', input['Product']['Key'])
    sds_metadata = get_sds_metadata(input['Metadata'])
    umm_json = get_granule_data(sds_metadata, config)
    output_location = {
        'bucket': config['output_bucket'],
        'key': umm_json['GranuleUR'] + '.umm_json',
    }
    upload_content_to_s3(output_location, json.dumps(umm_json))

    return output_location


def lambda_handler(event, context):
    output = create_granule_echo10_in_s3(event, CONFIG)
    return output
