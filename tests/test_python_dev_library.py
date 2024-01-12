from pathlib import Path

import shutil

from components.python_dev_library import PythonDevLibraryManager

from testing_common import TESTDATA, is_dillable, get_repo


def test_blender_dev_directory_addon_class():
    repo = get_repo()
    deploy_dir = Path(TESTDATA['temp_dir']) / 'deploy'
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)

    # Test creating a BlenderRegularScript object
    result = PythonDevLibraryManager.create(Path(TESTDATA['python_dev_library|0|path']),
                                            name=TESTDATA['python_dev_library|0|library_name'])
    assert result, 'PythonDevLibraryManager should be able to create a PythonDevLibrary object'
    python_dev_lib = result.data
    repo.add_component(python_dev_lib)
    result = python_dev_lib.deploy(deploy_dir)
    assert result, 'Error deploying PythonDevLibrary as a symlink'
    deployed_path = deploy_dir / python_dev_lib.name
    assert deployed_path.exists(), 'PythonDevLibrary should be deployed to deploy dir'

    # Test dill-ability
    assert is_dillable(python_dev_lib), 'PythonDevLibrary should be dillable'
