from pathlib import Path
import shutil

from packaging.version import Version

from testing_common import TESTDATA, is_dillable

from components.blender_program import BlenderProgram
from components.blender_venv import BlenderVenv, BlenderVenvManager
from components.python_package import PythonPyPIPackage, PythonLocalPackage, PythonLibrary, PythonPackageSet


def test_blender_venv_class():
    # This test will only succeed if Blender is installed at the given path.
    blender_venv_path = Path(TESTDATA['blender_venv|0|blender_venv_path'])
    if blender_venv_path.exists():
        venv = BlenderVenv(blender_venv_path, store_in_pool=True)
        assert venv.blender_program.blender_version == Version(TESTDATA['blender_venv|0|blender_version'])

        # Test pth related methods
        pth_path = venv.venv_path / venv.venv_managed_packages_pth_path
        venv.remove_venv_pth()
        assert not pth_path.exists(), 'BlenderVenv.remove_venv_pth() should remove the venv pth file'
        venv.add_bpy_package_to_venv_pth()
        assert pth_path.exists(), 'BlenderVenv.add_bpy_package_to_venv_pth() should create the venv pth file'
        pth_path = venv.blender_program.python_site_pacakge_dir / venv.venv_managed_packages_pth_path.name
        venv.remove_blender_pth()
        assert not pth_path.exists(), 'BlenderVenv.remove_blender_pth() should remove the blender pth file'
        venv.add_bpy_package_to_blender_pth()
        venv.add_site_packages_to_blender_pth()
        assert pth_path.exists(), 'BlenderVenv.add_bpy_package_to_blender_pth() should create the blender pth file'
        # venv.add_local_libraries_to_venv_pth()  TODO: Test when local libraries are implemented
        # venv.add_local_libraries_to_blender_pth()

        # Test dill-ability
        assert is_dillable(venv), 'BlenderVenv should be picklable'


def test_blender_venv_manager_class():
    # Test BlenderVenvManager.create_blender_venv()
    # This test will only succeed if Blender is installed at the given path.
    blender_exe_path = Path(TESTDATA['blender_program|0|blender_exe_path'])
    venv_path = Path(__file__).parent / 'test_blender_venv'
    if venv_path.exists():  # Remove the test venv if it exists
        shutil.rmtree(venv_path)
    blender_program = BlenderProgram(blender_exe_path)
    blender_venv = BlenderVenvManager.create_blender_venv(blender_program, venv_path)
    assert Path(blender_venv.venv_config['base-executable']) == blender_program.python_exe_path
    result = blender_venv.install_bpy_package()
    assert result.ok, f'Error installing bpy package: {result.message}'
    result = blender_venv.install_site_pacakge(PythonPyPIPackage('scipy'))
    assert result.ok, f'Error installing site package: {result.message}'
    result = blender_venv.install_site_pacakge(PythonPackageSet('packaging\nutm\nshapely'))
    assert result.ok, f'Error installing site package: {result.message}'

    # Remove the test venv directory
    shutil.rmtree(venv_path)

