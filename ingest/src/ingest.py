#!/usr/bin/env python3
import os
import zipfile
from logging import getLogger
from mimetypes import guess_type

import boto3
from boto3.s3.transfer import TransferConfig


log = getLogger(__name__)


def upload_to_s3(bucket, key, transfer_config):
    log.info('Uploading %s', key)
    s3 = boto3.client('s3')
    content_type = guess_type(key)[0]
    s3.upload_file(key, bucket, key, ExtraArgs={'ContentType': content_type}, Config=transfer_config)


def copy_s3_object(copy_source, dest_bucket, dest_key):
    log.info('Copying %s', dest_key)
    s3 = boto3.client('s3')
    content_type = guess_type(dest_key)[0]
    s3.copy_object(CopySource=copy_source, Bucket=dest_bucket, Key=dest_key, ContentType=content_type, MetadataDirective='REPLACE')


def download_s3_object_collection(collection, product_name, transfer_config):
    log.info('Downloading product files')

    local_files = []
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(collection['Bucket'])
    prefix = collection.get('Prefix', '')

    for key in collection['Keys']:
        local_file_name = os.path.join(product_name, key)
        directory = os.path.dirname(local_file_name)
        if not os.path.exists(directory):
            os.makedirs(directory)
        full_key = os.path.join(prefix, key)
        bucket.download_file(full_key, local_file_name, Config=transfer_config)
        local_files.append(local_file_name)

    return local_files


def create_zip_archive(zip_file_name, files):
    log.info('Creating %s', zip_file_name)
    with zipfile.ZipFile(zip_file_name, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zip_file:
        for f in files:
            zip_file.write(f)


def process_task(task_input, job_config):
    output = {}
    output_products = {}
    transfer_config = TransferConfig(**job_config['transfer_config'])

    product_name = task_input['ProductName']
    log.info('Processing %s', product_name)

    metadata_output_key = product_name + os.path.splitext(task_input['Metadata']['Key'])[1]
    copy_s3_object(task_input['Metadata'], job_config['metadata_bucket'], metadata_output_key)

    browse_output_key = product_name + os.path.splitext(task_input['Browse']['Key'])[1]
    copy_s3_object(task_input['Browse'], job_config['browse_bucket'], browse_output_key)

    local_files = download_s3_object_collection(task_input['ProductFiles'], product_name, transfer_config)

    output_zip_name = '{0}.zip'.format(product_name)
    create_zip_archive(output_zip_name, local_files)
    upload_to_s3(job_config['product_bucket'], output_zip_name, transfer_config)
    os.remove(output_zip_name)
    output_products['all'] = output_zip_name

    for derived_product in job_config['derived_products']:
        output_zip_name = '{0}.{1}.zip'.format(product_name, derived_product['name'])
        files = [os.path.join(product_name, f) for f in derived_product['files'] if f in local_files]
        create_zip_archive(output_zip_name, files)
        upload_to_s3(job_config['product_bucket'], output_zip_name, transfer_config)
        os.remove(output_zip_name)
        output_products[derived_product['name']] = output_zip_name

    for label, output_product in output_products.items():
        output[label] = {
            'Product': {
                'Bucket': job_config['product_bucket'],
                'Key': output_product,
            },
            'Metadata': {
                'Bucket': job_config['metadata_bucket'],
                'Key': metadata_output_key,
            },
            'Browse': {
                'Bucket': job_config['browse_bucket'],
                'Key': browse_output_key,
            }
        }

    log.info('Done processing %s', product_name)
    return output
