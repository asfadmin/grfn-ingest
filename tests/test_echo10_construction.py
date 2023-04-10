import json

import main


def test_get_file_content_from_s3(inputs):
    content1 = b'{\n  "label": "S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6",\n' \
               b'  "location": {\n' \
               b'    "type": "Polygon",\n' \
               b'    "coordinates": [\n      [\n        [\n          -175.564331,\n          51.22303\n        ],\n' \
               b'        [\n          -179.13033705784176,\n          51.61511015273788\n        ],\n' \
               b'        [\n          -178.851135,\n          52.739079\n        ],\n' \
               b'        [\n          -175.19286980698257,\n          52.345011494426714\n        ],\n' \
               b'        [\n          -175.564331,\n          51.22303\n        ]\n      ]\n    ]\n  },\n' \
               b'  "creation_timestamp": "2023-03-23T00:34:17.970611Z",\n' \
               b'  "version": "2.0.6",\n  "metadata": {\n' \
               b'    "ogr_bbox": [\n      [\n        -179.13033705784176,\n        51.22303\n      ],\n' \
               b'      [\n        -175.19286980698257,\n        51.22303\n      ],\n' \
               b'      [\n        -175.19286980698257,\n        52.739079\n      ],\n' \
               b'      [\n        -179.13033705784176,\n        52.739079\n      ]\n    ],\n' \
               b'    "reference_scenes": [\n' \
               b'      "S1A_IW_SLC__1SDV_20201118T180243_20201118T180302_035306_041FCE_A92A"\n    ],\n' \
               b'    "secondary_scenes": [\n' \
               b'      "S1A_IW_SLC__1SDV_20201013T180243_20201013T180302_034781_040D9A_B884"\n    ],\n' \
               b'    "sensing_start":' \
               b' "2020-11-18T18:02:43.000000Z",\n    "sensing_stop": "2020-11-18T18:03:02.000000Z",\n' \
               b'    "orbit_number": [\n      35306,\n      34781\n    ],\n    "platform": [\n      "Sentinel-1A",\n' \
               b'      "Sentinel-1A"\n    ],\n    "beam_mode": "IW",\n    "orbit_direction": "descending",\n' \
               b'    "dataset_type": "slc",\n    "product_type": "interferogram",\n    "polarization": "HH",\n' \
               b'    "look_direction": "right",\n    "track_number": 59,\n    "perpendicular_baseline": 13.7661\n  }\n}'
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

    mocker.patch('main.now', return_value='2023-01-01T00:00:00Z')
    with open(f'{test_data_dir}/S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.json') as f:
        content = json.load(f)

    mocker.patch('main.get_sds_metadata', return_value=content)

    mocker.patch('main.get_s3_file_size', return_value=49203991)

    # data1 must be defined before
    data1 = {'granule_ur': 'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6',
             'insert_time': '2023-01-01T00:00:00Z',
             'last_update': '2023-01-01T00:00:00Z',
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
               'PROCESSING_DESCRIPTION': 'Sentinel-1 SLC interferometric products generated by JPL using ISCE v2.0.0,'
                                         ' delivered by ASF',
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
    data = main.get_granule_data(inputs, config['granule_data'])
    assert data == data1


def test_render_granule_data_as_echo10():
    content1 = '<Granule xmlns:html="http://www.w3.org/1999/xhtml" xmlns:xsi="http://www.w3.org/2001/' \
               'XMLSchema-instance" xsi:noNamespaceSchemaLocation="">\n' \
              '    <GranuleUR>S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6' \
               '</GranuleUR>\n' \
              '    <InsertTime>2023-01-01T00:00:00Z</InsertTime>\n    <LastUpdate>2023-01-01T00:00:00Z</LastUpdate>\n' \
              '    <Collection>\n        <DataSetId>Sentinel-1 Interferograms (BETA)</DataSetId>\n    </Collection>\n' \
              '    <DataGranule>\n        \n        <SizeMBDataGranule>46.92458248138428</SizeMBDataGranule>\n' \
              '        \n' \
              '        <ProducerGranuleId>S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6' \
               '</ProducerGranuleId>\n' \
              '        <DayNightFlag>UNSPECIFIED</DayNightFlag>\n' \
               '        <ProductionDateTime>2023-03-23T00:34:17.970611Z</ProductionDateTime>\n' \
              '    </DataGranule>\n    <Temporal>\n        <RangeDateTime>\n' \
              '            <BeginningDateTime>2020-11-18T18:02:43.000000Z</BeginningDateTime>\n' \
              '            <EndingDateTime>2020-11-18T18:03:02.000000Z</EndingDateTime>\n' \
              '        </RangeDateTime>\n    </Temporal>\n    <Spatial>\n        <HorizontalSpatialDomain>\n' \
              '            <Geometry>\n                <GPolygon>\n                  <Boundary> \n' \
              '                  \n                    <Point>\n' \
              '                    <PointLongitude>-175.564331</PointLongitude>\n' \
              '                    <PointLatitude>51.22303</PointLatitude>\n                    </Point>\n' \
              '                  \n                    <Point>\n' \
              '                    <PointLongitude>-179.13033705784176</PointLongitude>\n' \
              '                    <PointLatitude>51.61511015273788</PointLatitude>\n' \
              '                    </Point>\n                  \n                    <Point>\n' \
              '                    <PointLongitude>-178.851135</PointLongitude>\n' \
              '                    <PointLatitude>52.739079</PointLatitude>\n                    </Point>\n' \
              '                  \n                    <Point>\n' \
              '                    <PointLongitude>-175.19286980698257</PointLongitude>\n' \
              '                    <PointLatitude>52.345011494426714</PointLatitude>\n' \
              '                    </Point>\n                  \n                </Boundary>\n' \
              '                </GPolygon>\n            </Geometry>\n        </HorizontalSpatialDomain>\n' \
              '    </Spatial>\n    <OrbitCalculatedSpatialDomains>\n        \n' \
              '        <OrbitCalculatedSpatialDomain>\n          <OrbitNumber>35306</OrbitNumber>\n' \
              '        </OrbitCalculatedSpatialDomain>\n        \n        <OrbitCalculatedSpatialDomain>\n' \
              '          <OrbitNumber>34781</OrbitNumber>\n        </OrbitCalculatedSpatialDomain>\n' \
              '        \n    </OrbitCalculatedSpatialDomains>\n    <Platforms>\n        \n        <Platform>\n' \
              '            <ShortName>SENTINEL-1A</ShortName>\n            <Instruments>\n' \
              '                <Instrument>\n                    <ShortName>SENTINEL-1A C-Band SAR</ShortName>\n' \
              '                    <Sensors>\n                        <Sensor>\n' \
              '                            <ShortName>IW</ShortName>\n                        </Sensor>\n' \
              '                    </Sensors>\n                </Instrument>\n            </Instruments>\n' \
              '        </Platform>\n        \n    </Platforms>\n    <AdditionalAttributes>\n        \n' \
              '        <AdditionalAttribute>\n            <Name>GROUP_ID</Name>\n            <Values>\n' \
              '                \n                    <Value>' \
               'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6</Value>\n' \
              '                \n            </Values>\n        </AdditionalAttribute>\n        \n' \
              '        <AdditionalAttribute>\n            <Name>ASCENDING_DESCENDING</Name>\n            <Values>\n' \
              '                \n                    <Value>descending</Value>\n                \n' \
              '            </Values>\n        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
              '            <Name>BEAM_MODE_TYPE</Name>\n            <Values>\n                \n' \
              '                    <Value>slc</Value>\n                \n            </Values>\n' \
              '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
              '            <Name>BEAM_MODE</Name>\n            <Values>\n                \n' \
              '                    <Value>IW</Value>\n                \n            </Values>\n' \
              '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
              '            <Name>BEAM_MODE_DESC</Name>\n            <Values>\n                \n' \
              '                    <Value>interferogram</Value>\n                \n            </Values>\n' \
              '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
              '            <Name>POLARIZATION</Name>\n            <Values>\n                \n' \
              '                    <Value>HH</Value>\n                \n            </Values>\n' \
              '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
              '            <Name>LOOK_DIRECTION</Name>\n            <Values>\n                \n' \
              '                    <Value>right</Value>\n                \n            </Values>\n' \
              '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
              '            <Name>PATH_NUMBER</Name>\n            <Values>\n                \n' \
              '                    <Value>59</Value>\n                \n            </Values>\n' \
              '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
              '            <Name>BYTES</Name>\n            <Values>\n                \n' \
              '                    <Value>49203991</Value>\n                \n            </Values>\n' \
              '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
              '            <Name>NEAR_START_LON</Name>\n            <Values>\n                \n' \
               '                    <Value>-179.13033705784176</Value>\n                \n' \
               '            </Values>\n        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
               '            <Name>NEAR_START_LAT</Name>\n            <Values>\n                \n' \
               '                    <Value>51.22303</Value>\n                \n            </Values>\n' \
               '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
               '            <Name>FAR_START_LON</Name>\n            <Values>\n                \n' \
               '                    <Value>-175.19286980698257</Value>\n                \n            </Values>\n' \
               '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
               '            <Name>FAR_START_LAT</Name>\n            <Values>\n                \n' \
               '                    <Value>51.22303</Value>\n                \n            </Values>\n' \
               '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
               '            <Name>FAR_END_LON</Name>\n            <Values>\n                \n' \
               '                    <Value>-175.19286980698257</Value>\n                \n            </Values>\n' \
               '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
               '            <Name>FAR_END_LAT</Name>\n            <Values>\n                \n' \
               '                    <Value>52.739079</Value>\n                \n            </Values>\n' \
               '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
               '            <Name>NEAR_END_LON</Name>\n            <Values>\n                \n' \
               '                    <Value>-179.13033705784176</Value>\n                \n            </Values>\n' \
               '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
               '            <Name>NEAR_END_LAT</Name>\n            <Values>\n                \n' \
               '                    <Value>52.739079</Value>\n                \n            </Values>\n' \
               '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
               '            <Name>ASF_PLATFORM</Name>\n            <Values>\n                \n' \
               '                    <Value>Sentinel-1 Interferogram (BETA)</Value>\n                \n' \
               '            </Values>\n        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
               '            <Name>PROCESSING_TYPE</Name>\n            <Values>\n                \n' \
               '                    <Value>GUNW_STD</Value>\n                \n            </Values>\n' \
               '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
               '            <Name>PROCESSING_TYPE_DISPLAY</Name>\n            <Values>\n                \n' \
               '                    <Value>Standard Product, NetCDF</Value>\n                \n' \
               '            </Values>\n        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
               '            <Name>PROCESSING_DESCRIPTION</Name>\n            <Values>\n                \n' \
               '                    <Value>Sentinel-1 SLC interferometric products generated by' \
               ' JPL using ISCE v2.0.0, delivered by ASF</Value>\n                \n            </Values>\n' \
               '        </AdditionalAttribute>\n        \n        <AdditionalAttribute>\n' \
               '            <Name>THUMBNAIL_URL</Name>\n            <Values>\n                \n' \
               '                    <Value>https://grfn-public-test.asf.alaska.edu/' \
               'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.png</Value>\n' \
               '                \n            </Values>\n        </AdditionalAttribute>\n        \n' \
               '        <AdditionalAttribute>\n            <Name>PERPENDICULAR_BASELINE</Name>\n' \
               '            <Values>\n                \n                    <Value>13.7661</Value>\n' \
               '                \n            </Values>\n        </AdditionalAttribute>\n        \n' \
               '        <AdditionalAttribute>\n            <Name>MISSION_NAME</Name>\n            <Values>\n' \
               '                \n                    <Value>S1 I-grams (BETA) - Other</Value>\n                \n' \
               '            </Values>\n        </AdditionalAttribute>\n        \n    </AdditionalAttributes>\n' \
               '    <InputGranules>\n        \n' \
               '        <InputGranule>[Reference] S1A_IW_SLC__1SDV_20201118T180243_20201118T180302_035306_041FCE_A92A' \
               '</InputGranule>\n        \n' \
               '        <InputGranule>[Secondary]' \
               ' S1A_IW_SLC__1SDV_20201013T180243_20201013T180302_034781_040D9A_B884</InputGranule>\n        \n' \
               '    </InputGranules>\n    <OnlineAccessURLs>\n        <OnlineAccessURL>\n' \
               '            <URL>https://grfn-test.asf.alaska.edu/door/download/' \
               'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.nc</URL>\n' \
               '        </OnlineAccessURL>\n    </OnlineAccessURLs>\n    <Orderable>true</Orderable>\n' \
               '    <Visible>true</Visible>\n    <AssociatedBrowseImageUrls>\n        <ProviderBrowseUrl>\n' \
               '            <URL>https://grfn-public-test.asf.alaska.edu/' \
               'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.png</URL>\n' \
               '        </ProviderBrowseUrl>\n    </AssociatedBrowseImageUrls>\n</Granule>\n'

    data = {'granule_ur': 'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6',
            'insert_time': '2023-01-01T00:00:00Z',
            'last_update': '2023-01-01T00:00:00Z',
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
               'PROCESSING_DESCRIPTION': 'Sentinel-1 SLC interferometric products generated by JPL using ISCE v2.0.0,'
                                         ' delivered by ASF',
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
    content = main.render_granule_data_as_echo10(data)
    assert content == content1


def test_create_granule_echo10_in_s3(inputs, config, mocker):

    data1 = {'granule_ur': 'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6',
             'insert_time': '2023-01-01T00:00:00Z',
             'last_update': '2023-01-01T00:00:00Z',
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
    # mocker.patch('main.TEMPLATE_FILE', return_value='./echo10-construction/src/echo10.template')
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
