import io
import json
import unittest.mock

import pytest
from botocore.stub import Stubber

import echo10_construction


@pytest.fixture
def s3_stubber():
    with Stubber(echo10_construction.s3.meta.client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def test_get_file_content_from_s3(s3_stubber):
    s3_stubber.add_response(
        method='get_object',
        expected_params={'Bucket': 'myBucket', 'Key': 'myKey'},
        service_response={'Body': io.StringIO('myContent')}
    )
    assert echo10_construction.get_file_content_from_s3('myBucket', 'myKey') == 'myContent'


def test_write_to_file(tmp_path):
    target = tmp_path / 'foo.txt'
    echo10_construction.write_to_file(str(target), 'hello world')
    assert target.exists()
    assert target.read_text() == 'hello world'


def test_get_s3_file_size(s3_stubber):
    obj = {
        'Bucket': 'myBucket',
        'Key': 'myKey'
    }
    s3_stubber.add_response(method='head_object', expected_params=obj, service_response={'ContentLength': 123})
    assert echo10_construction.get_s3_file_size(obj) == 123


def test_get_sds_metadata(test_data_dir, s3_stubber):
    obj = {
        'Bucket': 'ingest-test-aux',
        'Key': 'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.json'
    }

    sds_metadata_file = test_data_dir / 'sds_metadata.json'
    sds_metadata = json.loads(sds_metadata_file.read_text())

    with sds_metadata_file.open() as f:
        s3_stubber.add_response(method='get_object', expected_params=obj, service_response={'Body': f})
        assert echo10_construction.get_sds_metadata(obj) == sds_metadata


def test_create_granule_echo10_in_s3(test_data_dir, inputs, config, mocker):

    mocker.patch('echo10_construction.upload_content_to_s3')

    echo10_s3_objects = [{
        'bucket': 'ingest-test-aux',
        'key': 'S1-GUNW-A-R-072-tops-20171117_20171111-145939-00043E_00034N-PP-428e-v3_0_0.umm_json',
    }]

    assert echo10_construction.create_granule_echo10_in_s3(inputs, config) == echo10_s3_objects

    assert echo10_construction.upload_content_to_s3.mock_calls == [
        unittest.mock.call(
            echo10_s3_objects[0],
            (test_data_dir / 'granule.umm_json.').read_text(),
        ),
    ]
