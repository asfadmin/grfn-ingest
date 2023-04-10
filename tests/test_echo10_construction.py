import json

import main


def test_get_file_content_from_s3(inputs, test_data_dir):
    test_file = test_data_dir / 'sds_metadata.json'
    content1 = test_file.read_bytes()
    obj = inputs['Metadata']

    content = main.get_file_content_from_s3(obj['Bucket'], obj['Key'])

    assert content == content1


def test_write_to_file(tmp_path):
    target = tmp_path / 'foo.txt'
    main.write_to_file(str(target), 'hello world')
    assert target.exists()
    assert target.read_text() == 'hello world'


def test_get_s3_file_size():
    obj = {'Bucket': 'grfn-content-test',
           'Key': 'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.nc'}

    length = main.get_s3_file_size(obj)
    assert length == 49203991


def test_get_sds_metadata():
    obj = {'Bucket': 'ingest-test-aux',
           'Key': 'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.json'}
    sds_metadata1 = {
        'label': 'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6',
        'location': {'type': 'Polygon',
                     'coordinates': [[[-175.564331, 51.22303], [-179.13033705784176, 51.61511015273788],
                                      [-178.851135, 52.739079], [-175.19286980698257, 52.345011494426714],
                                      [-175.564331, 51.22303]]]},
        'creation_timestamp': '2023-03-23T00:34:17.970611Z',
        'version': '2.0.6',
        'metadata': {'ogr_bbox': [[-179.13033705784176, 51.22303], [-175.19286980698257, 51.22303],
                                  [-175.19286980698257, 52.739079], [-179.13033705784176, 52.739079]],
                     'reference_scenes': ['S1A_IW_SLC__1SDV_20201118T180243_20201118T180302_035306_041FCE_A92A'],
                     'secondary_scenes': ['S1A_IW_SLC__1SDV_20201013T180243_20201013T180302_034781_040D9A_B884'],
                     'sensing_start': '2020-11-18T18:02:43.000000Z',
                     'sensing_stop': '2020-11-18T18:03:02.000000Z',
                     'orbit_number': [35306, 34781],
                     'platform': ['Sentinel-1A', 'Sentinel-1A'],
                     'beam_mode': 'IW',
                     'orbit_direction': 'descending',
                     'dataset_type': 'slc',
                     'product_type': 'interferogram',
                     'polarization': 'HH',
                     'look_direction': 'right',
                     'track_number': 59,
                     'perpendicular_baseline': 13.7661}}
    sds_metadata = main.get_sds_metadata(obj)
    assert sds_metadata == sds_metadata1


def test_get_mission(config):
    polygon = [[-175.564331, 51.22303], [-179.13033705784176, 51.61511015273788],
               [-178.851135, 52.739079], [-175.19286980698257, 52.345011494426714]]

    mission = main.get_mission(polygon, config['granule_data']['missions'])
    mission1 = 'S1 I-grams (BETA) - Other'
    assert mission == mission1


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
    echo10_file = test_data_dir / 'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.echo10'
    content = echo10_file.read_text()

    granule_data_file = test_data_dir / 'granule_data.json'
    granule_data = json.loads(granule_data_file.read_text())
    assert main.render_granule_data_as_echo10(granule_data) == content


def test_create_granule_echo10_in_s3(inputs, config, mocker):

    data1 = {'granule_ur': 'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6',
             'insert_time': '2023-04-07T18:23:39Z',
             'last_update': '2023-04-07T18:23:39Z',
             'collection': 'Sentinel-1 Interferograms (BETA)',
             'size_mb_data_granule': 46.92458248138428,
             'producer_granule_id': 'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6',
             'production_date_time': '2023-03-23T00:34:17.970611Z',
             'beginning_date_time': '2020-11-18T18:02:43.000000Z',
             'ending_date_time': '2020-11-18T18:03:02.000000Z',
             'orbits': [35306, 34781],
             'platforms': ['SENTINEL-1A'],
             'sensor_short_name': 'IW',
             'polygon': [[-175.564331, 51.22303], [-179.13033705784176, 51.61511015273788], [-178.851135, 52.739079],
                         [-175.19286980698257, 52.345011494426714]],
             'additional_attributes': {
                 'GROUP_ID': 'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6',
                 'ASCENDING_DESCENDING': 'descending',
                 'BEAM_MODE_TYPE': 'slc',
                 'BEAM_MODE': 'IW',
                 'BEAM_MODE_DESC': 'interferogram',
                 'POLARIZATION': 'HH',
                 'LOOK_DIRECTION': 'right',
                 'PATH_NUMBER': 59,
                 'BYTES': 49203991,
                 'NEAR_START_LON': -179.13033705784176,
                 'NEAR_START_LAT': 51.22303,
                 'FAR_START_LON': -175.19286980698257,
                 'FAR_START_LAT': 51.22303,
                 'FAR_END_LON': -175.19286980698257,
                 'FAR_END_LAT': 52.739079,
                 'NEAR_END_LON': -179.13033705784176,
                 'NEAR_END_LAT': 52.739079,
                 'ASF_PLATFORM': 'Sentinel-1 Interferogram (BETA)',
                 'PROCESSING_TYPE': 'GUNW_STD',
                 'PROCESSING_TYPE_DISPLAY': 'Standard Product, NetCDF',
                 'PROCESSING_DESCRIPTION': 'Sentinel-1 SLC interferometric products generated'
                                           ' by JPL using ISCE v2.0.0, delivered by ASF',
                 'THUMBNAIL_URL': 'https://grfn-public-test.asf.alaska.edu/'
                                  'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.png',
                 'PERPENDICULAR_BASELINE': 13.7661,
                 'MISSION_NAME': 'S1 I-grams (BETA) - Other'},
             'input_granules': [
                 '[Reference] S1A_IW_SLC__1SDV_20201118T180243_20201118T180302_035306_041FCE_A92A',
                 '[Secondary] S1A_IW_SLC__1SDV_20201013T180243_20201013T180302_034781_040D9A_B884'],
             'visible': 'true',
             'orderable': 'true',
             'online_access_url': 'https://grfn-test.asf.alaska.edu/door/download/'
                                  'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.nc',
             'browse_url': 'https://grfn-public-test.asf.alaska.edu/'
                           'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.png'
             }
    mocker.patch('main.get_granule_data', return_value=data1)
    mocker.patch('main.upload_content_to_s3', return_value=None)
    echo10_s3_objects1 =\
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

    echo10_s3_objects = main.create_granule_echo10_in_s3(inputs, config)
    assert echo10_s3_objects == echo10_s3_objects1
