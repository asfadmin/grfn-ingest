import io
import json
import unittest.mock

import pytest
from botocore.stub import Stubber

import metadata_construction


@pytest.fixture
def s3_stubber():
    with Stubber(metadata_construction.s3.meta.client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def test_get_file_content_from_s3(s3_stubber):
    s3_stubber.add_response(
        method='get_object',
        expected_params={'Bucket': 'myBucket', 'Key': 'myKey'},
        service_response={'Body': io.StringIO('myContent')}
    )
    assert metadata_construction.get_file_content_from_s3('myBucket', 'myKey') == 'myContent'


def test_write_to_file(tmp_path):
    target = tmp_path / 'foo.txt'
    metadata_construction.write_to_file(str(target), 'hello world')
    assert target.exists()
    assert target.read_text() == 'hello world'


def test_get_s3_file_size(s3_stubber):
    obj = {
        'Bucket': 'myBucket',
        'Key': 'myKey'
    }
    s3_stubber.add_response(method='head_object', expected_params=obj, service_response={'ContentLength': 123})
    assert metadata_construction.get_s3_file_size(obj) == 123


def test_get_sds_metadata(test_data_dir, s3_stubber):
    obj = {
        'Bucket': 'ingest-test-aux',
        'Key': 'S1-GUNW-D-R-123-tops-20240212_20240107-032647-00038E_00036N-PP-2e78-v3_0_0'
    }

    sds_metadata_file = test_data_dir / 'sds_metadata.json'
    sds_metadata = json.loads(sds_metadata_file.read_text())

    with sds_metadata_file.open() as f:
        s3_stubber.add_response(method='get_object', expected_params=obj, service_response={'Body': f})
        assert metadata_construction.get_sds_metadata(obj) == sds_metadata


def test_create_granule_metadata_in_s3(test_data_dir, inputs, config, mocker):
    mocker.patch('metadata_construction.now', return_value='2024-03-02T22:12:36.000Z')
    mocker.patch('metadata_construction.upload_content_to_s3')

    sds_metadata =json.loads((test_data_dir / 'sds_metadata.json').read_text())
    mocker.patch('metadata_construction.get_sds_metadata', return_value=sds_metadata)

    metadata_s3_object = {
        'bucket': 'ingest-test-aux',
        'key': 'S1-GUNW-D-R-123-tops-20240212_20240107-032647-00038E_00036N-PP-2e78-v3_0_0.umm_json',
    }

    assert metadata_construction.create_granule_metadata_in_s3(inputs, config) == metadata_s3_object

    assert metadata_construction.upload_content_to_s3.mock_calls == [
        unittest.mock.call(
            metadata_s3_object,
            json.dumps(json.loads((test_data_dir / 'granule.umm_json').read_text()), sort_keys=True),
        ),
    ]
