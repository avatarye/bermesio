from testing_common import *

from components.repository import Repository


def test_repository_class():
    repo = Repository()
    assert repo.is_repository_path_ready, 'Repository path is not ready'
    assert repo.has_internet_connection, 'No internet connection'
    assert is_dillable(repo), 'Repository should be picklable'
