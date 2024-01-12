from pathlib import Path
import shutil

from packaging.version import Version

from testing_common import TESTDATA, is_dillable, get_repo

from components.blender_program import BlenderProgram, BlenderProgramManager
from components.blender_venv import BlenderVenvManager
from components.python_package import PythonPyPIPackage, PythonPackageSet


def test_blender_venv_class():
    repo = get_repo()

    # Add BlenderProgram to repo first
    blender_dir_path = Path(TESTDATA['blender_program|0|blender_dir_path'])
    result = repo.create_component(BlenderProgram, blender_dir_path, name='Blender_4.02_Win')
    assert result, 'Error adding BlenderProgram to repo'

    # Add BlenderVenv to repo
    venv_path = repo.blender_venv_repo.storage_save_dir / 'TestBlenderVenv'
    if venv_path.exists():  # Remove the test venv if it exists
        shutil.rmtree(venv_path)
    blender_program = result.data
    blender_venv = BlenderVenvManager.create_venv_from_blender_program(blender_program, venv_path).data
    result = repo.add_component(blender_venv)
    assert result, f'Error adding BlenderVenv to repo: {result.message}'

    # Test package related functions
    blender_venv.install_bpy_package()
    assert str(blender_venv.bpy_package) == 'bpy==4.0.0', ('BlenderVenv.install_bpy_package() should install the bpy '
                                                           'package')
    blender_venv.install_site_package(PythonPyPIPackage('shapely'))
    assert 'shapely' in str(blender_venv.site_packages), ('BlenderVenv.install_site_package() should install the '
                                                           'shapely package')
    # TODO: Test install_dev_library()

    # Test pth related methods
    venv_pth_path = blender_venv.data_path / blender_venv.venv_managed_packages_pth_path
    blender_pth_path = (blender_venv.blender_program.data_path / blender_venv.blender_program.python_site_pacakge_dir
                        / blender_venv.venv_managed_packages_pth_path.name)
    blender_venv.add_bpy_package_to_venv_pth()
    blender_venv.add_dev_libraries_to_venv_pth()
    assert venv_pth_path.exists(), 'BlenderVenv.add_bpy_package_to_venv_pth() should create the venv pth file'
    blender_venv.add_bpy_package_to_blender_pth()
    blender_venv.add_site_packages_to_blender_pth()
    blender_venv.add_dev_libraries_to_blender_pth()
    assert blender_pth_path.exists(), 'BlenderVenv.add_bpy_package_to_blender_pth() should create the blender pth file'
    # NOTE: to thoroughly test the pth related methods, we should run the venv created above and test importing bpy and
    # shapely packages, and run above Blender GUI to test importing bpy and shapely packages.
    blender_venv.remove_venv_pth()
    assert not venv_pth_path.exists(), 'BlenderVenv.remove_venv_pth() should remove the venv pth file'
    blender_venv.remove_blender_pth()
    assert not blender_pth_path.exists(), 'BlenderVenv.remove_blender_pth() should remove the blender pth file'

    # Test dill-ability
    assert is_dillable(blender_venv), 'BlenderVenv should be picklable'


def test_blender_venv_manager_class():
    # Test venv creation function
    venv_path = Path(TESTDATA['temp_dir']) / 'test_blender_venv'
    if venv_path.exists():  # Remove the test venv if it exists
        shutil.rmtree(venv_path)

    blender_program = BlenderProgramManager.create(Path(TESTDATA['blender_program|0|blender_dir_path'])).data
    result = BlenderVenvManager.create_venv_from_blender_program(blender_program, venv_path)
    assert result, f'Error creating BlenderVenv: {result.message}'
