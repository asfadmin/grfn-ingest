import json
import os
from logging import getLogger
from mimetypes import guess_type

import boto3
from boto3.s3.transfer import TransferConfig


log = getLogger()
log.setLevel('INFO')
s3 = boto3.resource('s3')
config = json.loads(os.getenv('CONFIG'))


def copy_s3_object(copy_source, dest_bucket, dest_key, transfer_config):
    log.info('Copying %s', dest_key)
    content_type = guess_type(dest_key)[0]
    if not content_type:
        content_type = 'application/octet-stream'
    extra_args = {
        'ContentType': content_type,
        'MetadataDirective': 'REPLACE',
        'TaggingDirective': 'REPLACE',
    }
    s3.Bucket(dest_bucket).copy(CopySource=copy_source, Key=dest_key, ExtraArgs=extra_args, Config=transfer_config)


def lambda_handler(event, context):
    log.info('Processing %s', event['ProductName'])
    transfer_config = TransferConfig(**config['transfer_config'])

    metadata_output_key = event['ProductName'] + os.path.splitext(event['Metadata']['Key'])[1]
    copy_s3_object(event['Metadata'], config['metadata_bucket'], metadata_output_key, transfer_config)

    browse_output_key = event['ProductName'] + os.path.splitext(event['Browse']['Key'])[1]
    copy_s3_object(event['Browse'], config['browse_bucket'], browse_output_key, transfer_config)

    product_output_key = event['ProductName'] + os.path.splitext(event['Product']['Key'])[1]
    copy_s3_object(event['Product'], config['product_bucket'], product_output_key, transfer_config)

    output = {
        'Product': {
            'Bucket': config['product_bucket'],
            'Key': product_output_key,
        },
        'Metadata': {
            'Bucket': config['metadata_bucket'],
            'Key': metadata_output_key,
        },
        'Browse': {
            'Bucket': config['browse_bucket'],
            'Key': browse_output_key,
        }
    }
    log.info('Done processing %s', event['ProductName'])
    return output
