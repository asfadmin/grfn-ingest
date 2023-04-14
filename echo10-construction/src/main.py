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


def get_granule_data(inputs, config):
    sds_metadata = get_sds_metadata(inputs['Metadata'])
    granule_metadata = sds_metadata['metadata']

    collection = config['collection']
    granule_ur = sds_metadata['label']
    file_size = get_s3_file_size(inputs['Product'])
    browse_url = config['browse_path'].format(inputs['Browse']['Key'])
    online_access_url = config['download_path'].format(inputs['Product']['Key'])
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
        'platforms': [p.upper() for p in set(granule_metadata['platform'])],
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
            'VERSION': granule_metadata['version'],
        },
        'input_granules': input_granules,
        'visible': 'true',
        'orderable': 'true',
        'online_access_url': online_access_url,
        'browse_url': browse_url,
    }

    if granule_metadata['temporal_baseline_days'] != -1:
        data['additional_attributes']['TEMPORAL_BASELINE_DAYS'] = granule_metadata['temporal_baseline_days']

    if granule_metadata['weather_model'] != -1:
        data['additional_attributes']['WEATHER_MODEL'] = granule_metadata['weather_model']

    if granule_metadata['frame_number'] != -1:
        data['additional_attributes']['FRAME_NUMBER'] = granule_metadata['frame_number']

    return data


def render_granule_data_as_echo10(data):
    with open(TEMPLATE_FILE, 'r') as t:
        template_text = t.read()
    template = Template(template_text)
    return template.render(data)


def create_granule_echo10_in_s3(inputs, config):
    echo10_s3_objects = []
    log.info('Creating echo10 file for %s', inputs['Product']['Key'])
    granule_data = get_granule_data(inputs, config['granule_data'])
    echo10_content = render_granule_data_as_echo10(granule_data)
    echo10_s3_object = {
        'bucket': config['output_bucket'],
        'key': granule_data['granule_ur'] + '.echo10',
    }
    echo10_s3_objects.append(echo10_s3_object)
    upload_content_to_s3(echo10_s3_object, echo10_content)

    del granule_data['size_mb_data_granule']
    del granule_data['additional_attributes']['BYTES']

    for product in config['derived_products']:
        virtual_granule_data = copy.deepcopy(granule_data)
        log.info('Creating echo10 file for %s', inputs['Product']['Key'] + product['label'])
        virtual_granule_data['collection'] = product['dataset_id']
        virtual_granule_data['granule_ur'] = granule_data['granule_ur'] + '-' + product['label']
        virtual_granule_data['additional_attributes']['PROCESSING_TYPE'] = product['processing_type']
        virtual_granule_data['additional_attributes']['PROCESSING_TYPE_DISPLAY'] = product['processing_type_display']
        virtual_granule_data['online_access_url'] = '{0}?product={1}&amp;layer={2}'.format(
            config['api_url'], inputs['Product']['Key'], product['layer']
        )
        echo10_content = render_granule_data_as_echo10(virtual_granule_data)
        echo10_s3_object = {
            'bucket': config['output_bucket'],
            'key': virtual_granule_data['granule_ur'] + '.echo10',
        }
        echo10_s3_objects.append(echo10_s3_object)

        upload_content_to_s3(echo10_s3_object, echo10_content)

    return echo10_s3_objects


def lambda_handler(event, context):
    output = create_granule_echo10_in_s3(event, CONFIG)
    return output
