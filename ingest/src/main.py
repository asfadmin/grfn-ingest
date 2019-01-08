import os
import json
from logging import getLogger
from mimetypes import guess_type

import boto3
from boto3.s3.transfer import TransferConfig


def copy_s3_object(copy_source, dest_bucket, dest_key):
    log.info('Copying %s', dest_key)
    content_type = guess_type(dest_key)[0]
    if not content_type:
        content_type = 'application/octet-stream'
    s3.copy_object(CopySource=copy_source, Bucket=dest_bucket, Key=dest_key, ContentType=content_type, MetadataDirective='REPLACE') #TODO deal with transfer config


log = getLogger()
log.setLevel('INFO')
s3 = boto3.client('s3')
config = json.loads(os.getenv('CONFIG'))
transfer_config = TransferConfig(**config['transfer_config'])


def lambda_handler(event, context):
    log.info('Processing %s', event['ProductName'])

    metadata_output_key = event['ProductName'] + os.path.splitext(event['Metadata']['Key'])[1]
    copy_s3_object(event['Metadata'], config['metadata_bucket'], metadata_output_key)

    browse_output_key = event['ProductName'] + os.path.splitext(event['Browse']['Key'])[1]
    copy_s3_object(event['Browse'], config['browse_bucket'], browse_output_key)

    product_output_key = event['ProductName'] + os.path.splitext(event['Product']['Key'])[1]
    copy_s3_object(event['Product'], config['product_bucket'], product_output_key)

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
