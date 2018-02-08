import boto3
import os
import re
import json
from jinja2 import Template
from datetime import datetime
from logging import getLogger
from shapely.geometry import Polygon


log = getLogger()


TEMPLATE_FILE = 'echo10.template'


def setup():
    config = json.loads(os.environ['CONFIG'])
    log.setLevel(config['log_level'])
    log.debug('Config: {0}'.format(config))
    return config


def now():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def get_file_content_from_s3(bucket, key):
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket, key)
    response = obj.get()
    contents = response['Body'].read()
    return contents


def write_to_file(file_name, content):
    with open(file_name, 'w') as f:
        f.write(content)


def upload_file_to_s3(local_file, bucket, key, content_type='application/xml'):
    s3 = boto3.client('s3')
    s3.upload_file(local_file, bucket, key, ExtraArgs={'ContentType': content_type})


def upload_content_to_s3(s3_object, content):
    local_file = os.path.join('/tmp', s3_object['key'])
    write_to_file(local_file, content)
    upload_file_to_s3(local_file, s3_object['bucket'], s3_object['key'])


def get_s3_file_size(obj):
    s3 = boto3.resource('s3')
    obj = s3.Object(obj['Bucket'], obj['Key'])
    return obj.content_length


def get_sds_metadata(obj):
    content = get_file_content_from_s3(obj['Bucket'], obj['Key'])
    sds_metadata = json.loads(content)
    return sds_metadata


def get_mission(bbox, missions):
    granule = Polygon(bbox)
    for mission in missions:
        aoi = Polygon(mission['coords'])
        if granule.intersects(aoi):
            return mission['name']
    return None


def translate_asc_desc(value):
    if value == 'asc':
        return 'Ascending'
    if value == 'dsc':
        return 'Descending'
    return value


def get_config_value(config, key):
    if key in config:
        return config[key]
    else:
        return config['default']


def get_collection(config, zip_file_name):
    regex = re.compile('.*?\.?(unw_geo|full_res)?\.zip')
    file_type = regex.match(zip_file_name).group(1)
    collection = get_config_value(config, file_type)
    return collection


def get_granule_data(inputs, config):
    sds_metadata = get_sds_metadata(inputs['Metadata'])
    granule_metadata = sds_metadata['metadata']

    collection = get_collection(config['collections'], inputs['Product']['Key'])
    granule_ur = sds_metadata['label'] + '-' + collection['processing_type']
    file_size = get_s3_file_size(inputs['Product'])
    browse_url = config['browse_path'].format(inputs['Browse']['Key'])
    online_access_url = config['download_path'].format(inputs['Product']['Key'])
    mission = get_mission(granule_metadata['bbox'], config['missions'])

    input_granules = ['[Master] {0}'.format(g) for g in granule_metadata['master_scenes']]
    input_granules += ['[Slave] {0}'.format(g) for g in granule_metadata['slave_scenes']]

    data = {
        'granule_ur': granule_ur,
        'insert_time': now(),
        'last_update': now(),
        'collection': collection['dataset_id'],
        'size_mb_data_granule': float(file_size) / 1024 / 1024,
        'producer_granule_id': sds_metadata['label'],
        'production_date_time': sds_metadata['creation_timestamp'],
        'beginning_date_time': granule_metadata['sensingStart'],
        'ending_date_time': granule_metadata['sensingStop'],
        'orbits': granule_metadata['orbitNumber'],
        'platforms': [p.upper() for p in set(granule_metadata['platform'])],
        'sensor_short_name': granule_metadata['beamMode'],
        'polygon': sds_metadata['location']['coordinates'][0][:-1],
        'additional_attributes': {
            'GROUP_ID': sds_metadata['label'].replace('.', '-'),
            'ASCENDING_DESCENDING': translate_asc_desc(granule_metadata['direction']),
            'BEAM_MODE_TYPE': granule_metadata['dataset_type'],
            'BEAM_MODE': granule_metadata['beamMode'],
            'BEAM_MODE_DESC': granule_metadata['product_type'],
            'POLARIZATION': granule_metadata['polarization'] if 'polarization' in granule_metadata else 'UNSPECIFIED',
            'LOOK_DIRECTION': granule_metadata['lookDirection'],
            'PATH_NUMBER': granule_metadata['trackNumber'],
            'BYTES': file_size,
            'NEAR_START_LAT': granule_metadata['bbox'][0][1],
            'NEAR_START_LON': granule_metadata['bbox'][0][0],
            'FAR_START_LAT': granule_metadata['bbox'][1][1],
            'FAR_START_LON': granule_metadata['bbox'][1][0],
            'FAR_END_LAT': granule_metadata['bbox'][2][1],
            'FAR_END_LON': granule_metadata['bbox'][2][0],
            'NEAR_END_LAT': granule_metadata['bbox'][3][1],
            'NEAR_END_LON': granule_metadata['bbox'][3][0],
            'ASF_PLATFORM': 'Sentinel-1 Interferogram (BETA)',
            'PROCESSING_TYPE_DISPLAY': collection['processing_type_display'],
            'PROCESSING_DESCRIPTION': collection['processing_description'],
            'THUMBNAIL_URL': browse_url,
            'PERPENDICULAR_BASELINE': granule_metadata['perpendicularBaseline'],
            'SUB_SWATH': granule_metadata['swath'],
            'MISSION_NAME': mission,
        },
        'input_granules': input_granules,
        'visible': 'true',
        'orderable': 'true',
        'online_access_url': online_access_url,
        'browse_url': browse_url,
    }
    return data


def render_granule_data_as_echo10(data):
    with open(TEMPLATE_FILE, 'r') as t:
        template_text = t.read()
    template = Template(template_text)
    return template.render(data)


def create_granule_echo10_in_s3(inputs, config):
    log.info('Creating echo10 file for %s', inputs['Product']['Key'])
    granule_data = get_granule_data(inputs, config['granule_data'])
    echo10_content = render_granule_data_as_echo10(granule_data)
    echo10_s3_object = {
        'bucket': config['output_bucket'],
        'key': granule_data['granule_ur'] + '.echo10',
    }
    upload_content_to_s3(echo10_s3_object, echo10_content)
    return echo10_s3_object


def lambda_handler(event, context):
    config = setup()
    log.debug('Payload: {0}'.format(str(event)))
    output = create_granule_echo10_in_s3(event, config['echo10_construction'])
    return output
