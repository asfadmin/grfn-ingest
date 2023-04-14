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


def test_validate_metadata(mocker, monkeypatch):
    # TODO currently this fails when validating against the metadata schema, as expected;
    #  finish writing all test cases
    mocker.patch('verify.get_file_content_from_s3', return_value='{}')
    monkeypatch.chdir('verify/src/')
    verify.validate_metadata({'Bucket': None, 'Key': None})
