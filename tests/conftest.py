import shutil
from datetime import datetime
from pathlib import Path
import json
from uuid import uuid4

import pytest


@pytest.fixture(autouse=True)
def get_mock_job():
    def default_job(
            job_type='JOB_TYPE',
            request_time=datetime.now(),
            status_code='RUNNING',
            user_id='user',
            name='name',
            job_parameters=None,
            files=None,
            browse_images=None,
            thumbnail_images=None,
            expiration_time=None
    ):
        if job_parameters is None:
            job_parameters = {'param1': 'value1'}
        job_dict = {
            'job_type': job_type,
            'job_id': str(uuid4()),
            'request_time': request_time.isoformat(timespec='seconds'),
            'status_code': status_code,
            'user_id': user_id,
            'name': name,
            'job_parameters': job_parameters,
            'files': files,
            'browse_images': browse_images,
            'thumbnail_images': thumbnail_images,
            'expiration_time': expiration_time,
        }
        keys_to_delete = []
        for k, v in job_dict.items():
            if v is None:
                keys_to_delete.append(k)

        for key in keys_to_delete:
            del job_dict[key]

        return Job.from_dict(job_dict)
    return default_job


@pytest.fixture
def test_data_dir():
    data_dir = Path(__file__).resolve().parent / 'data'
    return data_dir


@pytest.fixture
def product_zip(tmp_path_factory, test_data_dir):
    tmp_dir = tmp_path_factory.mktemp('data')

    product_file = tmp_dir / 'product.zip'
    shutil.copy(test_data_dir / 'product.zip', product_file)

    return product_file


@pytest.fixture
def inputs():
    # pdb.set_trace()
    data_dir = Path(__file__).resolve().parent / 'data'
    with open(f'{data_dir}/inputs') as f:
        return json.load(f)


@pytest.fixture
def config():
    # pdb.set_trace()
    data_dir = Path(__file__).resolve().parent / 'data'
    with open(f'{data_dir}/config') as f:
        return json.load(f)


@pytest.fixture
def obj():
    return {'Bucket': 'grfn-content-test',
            'Key': 'S1-GUNW-D-R-059-tops-20201118_20201013-180252-00179W_00051N-PP-1ec8-v2_0_6.nc'}


@pytest.fixture
def polygon():
    return [[-175.564331, 51.22303], [-179.13033705784176, 51.61511015273788],
            [-178.851135, 52.739079], [-175.19286980698257, 52.345011494426714]]
