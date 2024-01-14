import json
import shutil
from pathlib import Path
import sys

import dill

from components.repository import Repository


class TestData:
    def __init__(self):
        test_data_json_path = Path(__file__).parent.parent / '_test_data/TestData.json'
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


def get_repo(repo_dir=None, delete_existing=True):
    if repo_dir is None:
        repo_dir = Path(TESTDATA["temp_dir"]) / 'test_repo'
        if repo_dir.exists() and delete_existing:
            shutil.rmtree(repo_dir)

    result = Repository(repo_dir).create_instance()
    if result:
        repo = result.data
        results = repo.init_sub_repos()
        if results:
            return repo
        else:
            raise Exception(f'Error initializing sub-repository: {result.message}')
    else:
        raise Exception(f'Error creating repository: {result.message}')
