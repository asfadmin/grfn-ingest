import json

import pytest

import verify


def test_get_file_content_from_s3(inputs, test_data_dir, s3_stubber):
    # FIXME this fails because the s3_stubber in conftest.py is only configured for
    #  the echo10-construction lambda
    test_file = test_data_dir / 'sds_metadata.json'
    content = test_file.read_text()

    obj = inputs['Metadata']

    with test_file.open() as f:
        s3_stubber.add_response(method='get_object', expected_params=obj, service_response={'Body': f})
        # assert verify.get_file_content_from_s3(obj['Bucket'], obj['Key']) == content
        assert False


def test_validate_metadata(test_data_dir, mocker, monkeypatch):
    monkeypatch.chdir('verify/src/')

    mocker.patch('verify.get_file_content_from_s3', return_value='{"foo":')
    with pytest.raises(verify.INVALID_METADATA, match=r'^Expecting value: line 1 column 8 \(char 7\)$'):
        verify.validate_metadata({'Bucket': None, 'Key': None})

    mocker.patch('verify.get_file_content_from_s3', return_value='{"foo": "bar"}')
    with pytest.raises(verify.INVALID_METADATA, match=r"^'label' is a required property$"):
        verify.validate_metadata({'Bucket': None, 'Key': None})

    # TODO add test case for v3

    sds_metadata_file = test_data_dir / 'sds_metadata.json'
    mocker.patch('verify.get_file_content_from_s3', return_value=sds_metadata_file.read_text())
    assert verify.validate_metadata({'Bucket': None, 'Key': None}) is None
