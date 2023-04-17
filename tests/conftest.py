import json
from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir():
    data_dir = Path(__file__).resolve().parent / 'data'
    return data_dir


@pytest.fixture
def inputs(test_data_dir):
    with open(f'{test_data_dir}/inputs.json') as f:
        return json.load(f)


@pytest.fixture
def config(test_data_dir):
    with open(f'{test_data_dir}/config.json') as f:
        return json.load(f)


