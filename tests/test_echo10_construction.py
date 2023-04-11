import json
import unittest.mock

import main


def test_get_file_content_from_s3(inputs, test_data_dir, s3_stubber):
    test_file = test_data_dir / 'sds_metadata.json'
    content = test_file.read_text()

    obj = inputs['Metadata']

    with test_file.open() as f:
        s3_stubber.add_response(method='get_object', expected_params=obj, service_response={'Body': f})
        assert main.get_file_content_from_s3(obj['Bucket'], obj['Key']) == content


def test_write_to_file(tmp_path):
    target = tmp_path / 'foo.txt'
    main.write_to_file(str(target), 'hello world')
    assert target.exists()
    assert target.read_text() == 'hello world'


def test_get_s3_file_size(s3_stubber):
    obj = {
        'Bucket': 'myBucket',
        'Key': 'myKey'
    }
    s3_stubber.add_response(method='head_object', expected_params=obj, service_response={'ContentLength': 123})
    assert main.get_s3_file_size(obj) == 123


def test_get_sds_metadata(test_data_dir, s3_stubber):
    obj = {
        'Bucket': 'ingest-test-aux',
        'Key': 'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.json'
    }

    sds_metadata_file = test_data_dir / 'sds_metadata.json'
    sds_metadata = json.loads(sds_metadata_file.read_text())

    with sds_metadata_file.open() as f:
        s3_stubber.add_response(method='get_object', expected_params=obj, service_response={'Body': f})
        assert main.get_sds_metadata(obj) == sds_metadata


def test_get_mission(config):
    polygon = [[-175.564331, 51.22303], [-179.13033705784176, 51.61511015273788],
               [-178.851135, 52.739079], [-175.19286980698257, 52.345011494426714]]

    assert main.get_mission(polygon, config['granule_data']['missions']) == 'S1 I-grams (BETA) - Other'


def test_get_granule_data(test_data_dir, inputs, config, mocker):

    mocker.patch('main.now', return_value='2023-04-07T18:23:39Z')

    sds_metadata_file = test_data_dir / 'sds_metadata.json'
    sds_metadata = json.loads(sds_metadata_file.read_text())
    mocker.patch('main.get_sds_metadata', return_value=sds_metadata)

    mocker.patch('main.get_s3_file_size', return_value=49203991)

    granule_data_file = test_data_dir / 'granule_data.json'
    granule_data = json.loads(granule_data_file.read_text())

    assert main.get_granule_data(inputs, config['granule_data']) == granule_data


def test_render_granule_data_as_echo10(test_data_dir):
    echo10_file = test_data_dir / 'granule.echo10'
    content = echo10_file.read_text()

    granule_data_file = test_data_dir / 'granule_data.json'
    granule_data = json.loads(granule_data_file.read_text())
    assert main.render_granule_data_as_echo10(granule_data) == content


def test_create_granule_echo10_in_s3(test_data_dir, inputs, config, mocker):

    granule_data_file = test_data_dir / 'granule_data.json'
    granule_data = json.loads(granule_data_file.read_text())
    mocker.patch('main.get_granule_data', return_value=granule_data)

    mocker.patch('main.upload_content_to_s3')

    echo10_s3_objects =\
        [{'bucket': 'ingest-test-aux', 'key':
            'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.echo10'},
         {'bucket': 'ingest-test-aux', 'key':
             'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6-unwrappedPhase.echo10'},
         {'bucket': 'ingest-test-aux', 'key':
             'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6-coherence.echo10'},
         {'bucket': 'ingest-test-aux', 'key':
             'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6-amplitude.echo10'},
         {'bucket': 'ingest-test-aux', 'key':
             'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6-connectedComponents.echo10'}]

    assert main.create_granule_echo10_in_s3(inputs, config) == echo10_s3_objects

    assert main.upload_content_to_s3.mock_calls == [
        unittest.mock.call(
            echo10_s3_objects[0],
            (test_data_dir / 'granule.echo10').read_text(),
        ),
        unittest.mock.call(
            echo10_s3_objects[1],
            (test_data_dir / 'granule-unwrappedPhase.echo10').read_text()
        ),
        unittest.mock.call(
            echo10_s3_objects[2],
            (test_data_dir / 'granule-coherence.echo10').read_text()
        ),
        unittest.mock.call(
            echo10_s3_objects[3],
            (test_data_dir / 'granule-amplitude.echo10').read_text()
        ),
        unittest.mock.call(
            echo10_s3_objects[4],
            (test_data_dir / 'granule-connectedComponents.echo10').read_text()
        ),
    ]
