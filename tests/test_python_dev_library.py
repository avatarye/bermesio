from pathlib import Path

from packaging.version import Version
import shutil

from components.python_dev_library import PythonDevLibrary, PythonDevLibraryManager

from testing_common import TESTDATA, is_dillable


def test_blender_dev_directory_addon_class():
    deploy_to_dir = Path(__file__).parent / 'test_python_dev_library' /'deploy'

    lib_path = Path(TESTDATA['python_dev_library|0|path'])
    lib_name = TESTDATA['python_dev_library|0|library_name']
    result = PythonDevLibraryManager.create_python_dev_library(lib_path, library_name=lib_name)
    assert result, 'PythonDevLibraryManager should be able to create a PythonDevLibrary object'
    lib = result.data
    assert lib.name == lib_name
    lib.deploy(deploy_to_dir)
    deployed_lib_paths = [f for f in deploy_to_dir.iterdir() if f.is_dir()]
    assert len(deployed_lib_paths) == 1, 'PythonDevLibrary should be deployed to the deploy directory'
    assert is_dillable(lib), 'PythonDevLibrary should be dillable'
    if deploy_to_dir.exists():
        shutil.rmtree(deploy_to_dir.parent)
