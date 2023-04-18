import json
from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir():
    data_dir = Path(__file__).resolve().parent / 'data' / 'v2'
    return data_dir


@pytest.fixture
def test_data_dir_v3():
    data_dir = Path(__file__).resolve().parent / 'data' / 'v3'
    return data_dir


@pytest.fixture
def inputs(test_data_dir):
    with open(f'{test_data_dir}/inputs.json') as f:
        return json.load(f)


@pytest.fixture
def config(test_data_dir):
    with open(f'{test_data_dir}/config.json') as f:
        return json.load(f)
