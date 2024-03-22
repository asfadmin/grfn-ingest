import json
import os
from datetime import datetime
from logging import getLogger

import boto3

log = getLogger()
log.setLevel('INFO')
CONFIG = json.loads(os.getenv('CONFIG'))

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
    return json.loads(content)


def format_polygon(polygon):
    coordinates = []
    for long, lat in reversed(polygon):
        coordinates.append({"Latitude": lat, "Longitude": long})
    return coordinates


def render_granule_metadata(sds_metadata, config, product) -> dict:
    granule_ur = sds_metadata['label']
    download_url = config['granule_data']['download_path']
    browse_url = config['granule_data']['browse_path']
    polygon = format_polygon(sds_metadata['location']['coordinates'][0])

    umm = {
        'MetadataSpecification': {
            'URL': 'https://cdn.earthdata.nasa.gov/umm/granule/v1.6.5',
            'Name': 'UMM-G',
            'Version': '1.6.5',
        },
        'GranuleUR': granule_ur,
        'CollectionReference': {
            'ShortName': 'ARIA_S1_GUNW',
            'Version': '1',
        },
        'RelatedUrls': [
            {
                'URL': f'{download_url}/{granule_ur}.nc',
                'Type': 'GET DATA',
            },
            {
                'URL': f'{browse_url}/{granule_ur}.png',
                'Type': 'GET RELATED VISUALIZATION',
            },
        ],
        'TemporalExtent': {
            'RangeDateTime': {
                'BeginningDateTime': sds_metadata['metadata']['sensing_start'],
                'EndingDateTime': sds_metadata['metadata']['sensing_stop'],
            },
        },
        'SpatialExtent': {
            'HorizontalSpatialDomain': {
                'Geometry': {
                    'GPolygons': [
                        {
                            'Boundary': {
                                'Points': polygon,
                            },
                        },
                    ],
                },
            },
        },
        'ProviderDates': [
            {
                'Date': now(),
                'Type': 'Insert',
            },
            {
                'Date': now(),
                'Type': 'Update',
            },
        ],
        "DataGranule": {
            "ArchiveAndDistributionInformation": [
                {
                    "Name": product['Key'],
                    "SizeInBytes": get_s3_file_size(product)
                }
            ],
            "DayNightFlag": "Unspecified",
            "ProductionDateTime": sds_metadata['creation_timestamp']
        },
        "Platforms": [
            {"ShortName": platform} for platform in sorted(set(sds_metadata['metadata']['platform']))
        ],
        "OrbitCalculatedSpatialDomains": [
            {"OrbitNumber": orbit} for orbit in sds_metadata['metadata']['orbit_number']
        ],
        "InputGranules": sds_metadata['metadata']['reference_scenes'] + sds_metadata['metadata']['secondary_scenes'],
        "AdditionalAttributes": [
            {"Name": "ASCENDING_DESCENDING", "Values": [sds_metadata['metadata']['orbit_direction']]},
            {"Name": "BEAM_MODE", "Values": [sds_metadata['metadata']['beam_mode']]},
            {"Name": "POLARIZATION", "Values": [sds_metadata['metadata']['polarization']]},
            {"Name": "PERPENDICULAR_BASELINE", "Values": [str(sds_metadata['metadata']['perpendicular_baseline'])]},
            {"Name": "VERSION", "Values": [sds_metadata['metadata']['version']]},
            {"Name": "FRAME_NUMBER", "Values": [str(sds_metadata['metadata']['frame_number'])]},
            {"Name": "PATH_NUMBER", "Values": [str(sds_metadata['metadata']['track_number'])]},
            {"Name": "TEMPORAL_BASELINE_DAYS", "Values": [str(sds_metadata['metadata']['temporal_baseline_days'])]}
        ]
    }

    if 'weather_model' in sds_metadata['metadata']:
        umm['AdditionalAttributes'].append({"Name": "WEATHER_MODEL",
                                            "Values": sds_metadata['metadata']['weather_model']})

    return umm


def create_granule_metadata_in_s3(inputs, config):
    log.info('Creating metadata file for %s', inputs['Product']['Key'])
    sds_metadata = get_sds_metadata(inputs['Metadata'])
    umm_json = render_granule_metadata(sds_metadata, config, inputs['Product'])
    output_location = {
        'bucket': config['output_bucket'],
        'key': umm_json['GranuleUR'] + '.umm.json',
    }
    upload_content_to_s3(output_location, json.dumps(umm_json, sort_keys=True))

    return output_location


def lambda_handler(event, context):
    output = create_granule_metadata_in_s3(event, CONFIG)
    return output
