import json
from pathlib import Path
import sys

import dill


class TestData:
    def __init__(self):
        test_data_json_path = Path(__file__).parent / 'TestData.json'
        if test_data_json_path.exists():
            with open(test_data_json_path, 'r') as f:
                self.test_data_json = json.load(f)
            self.test_data = self.test_data_json.get(sys.platform, {})
        else:
            raise FileNotFoundError('TestData.json not found. It should be located in the same folder as this file.')

    def __getitem__(self, key):
        keys = key.split('|')
        data = self.test_data
        for k in keys:
            if isinstance(data, list):
                data = data[int(k)]
            elif isinstance(data, dict):
                data = data.get(k)
            else:
                return data
            if data is None:
                return None
        return data


TESTDATA = TestData()


def is_dillable(obj):
    try:
        dill.dumps(obj)
        return True
    except Exception as e:
        print(f'{obj} is not dillable, {e}')
        return False
