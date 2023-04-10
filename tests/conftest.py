import json
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest

@pytest.fixture
def test_data_dir():
    data_dir = Path(__file__).resolve().parent / 'data'
    return data_dir


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
