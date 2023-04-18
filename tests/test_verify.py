import io

import pytest
from botocore.stub import Stubber

import verify


@pytest.fixture
def s3_stubber():
    with Stubber(verify.s3.meta.client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def test_get_file_content_from_s3(s3_stubber):
    s3_stubber.add_response(
        method='get_object',
        expected_params={'Bucket': 'myBucket', 'Key': 'myKey'},
        service_response={'Body': io.StringIO('myContent')}
    )
    assert verify.get_file_content_from_s3('myBucket', 'myKey') == 'myContent'


def test_validate_metadata(test_data_dir, mocker, monkeypatch):
    monkeypatch.chdir('verify/src/')

    mocker.patch('verify.get_file_content_from_s3', return_value='{"foo":')
    with pytest.raises(verify.INVALID_METADATA, match=r'^Expecting value: line 1 column 8 \(char 7\)$'):
        verify.validate_metadata({'Bucket': None, 'Key': None})

    mocker.patch('verify.get_file_content_from_s3', return_value='{"foo": "bar"}')
    with pytest.raises(verify.INVALID_METADATA, match=r"^'label' is a required property$"):
        verify.validate_metadata({'Bucket': None, 'Key': None})

    sds_metadata_file = test_data_dir / 'sds_metadata.json'
    mocker.patch('verify.get_file_content_from_s3', return_value=sds_metadata_file.read_text())
    assert verify.validate_metadata({'Bucket': None, 'Key': None}) is None

    sds_metadata_file_v3 = test_data_dir / 'sds_metadata_v3.json'
    mocker.patch('verify.get_file_content_from_s3', return_value=sds_metadata_file_v3.read_text())
    assert verify.validate_metadata({'Bucket': None, 'Key': None}) is None
