import json

import pytest

from main import *

@responses.activate
def test_get_granule_data(inputs, config):

    # data must be defined before
    assert get_granule_data(inputs, config) == data


    
