import json
from pathlib import Path

import pytest
from botocore.stub import Stubber

import main


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


@pytest.fixture
def s3_stubber():
    with Stubber(main.s3.meta.client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()