from pathlib import Path
import shutil

from packaging.version import Version

from test_common import *

from components.blender_program import BlenderProgram
from components.blender_venv import BlenderVenv, BlenderVenvManager


def test_blender_venv_class():
    # This test will only succeed if Blender is installed at the given path.
    blender_venv_path = Path(r'c:\TechDepot\Github\bermesio\_data\venvs\venv_blender_4.0.1_1')
    if blender_venv_path.exists():
        venv = BlenderVenv(blender_venv_path, store_in_pool=True)
        assert venv.blender_program.blender_version == Version('4.0.1')

        assert is_dillable(venv), 'BlenderVenv should be picklable'


def test_blender_venv_manager_class():
    # Test BlenderVenvManager.create_blender_venv()
    # This test will only succeed if Blender is installed at the given path.
    blender_exe_path = Path(r'c:\TechDepot\AvatarTools\Blender\Launcher\stable\blender-4.0.1-windows-x64\blender.exe')
    venv_path = Path(__file__).parent / 'test_blender_venv'
    if venv_path.exists():  # Remove the test venv if it exists
        shutil.rmtree(venv_path)
    blender_program = BlenderProgram(blender_exe_path)
    blender_venv = BlenderVenvManager.create_blender_venv(blender_program, venv_path)
    assert Path(blender_venv.blender_venv_config['base-executable']) == blender_program.python_exe_path
    # Remove the test venv directory
    shutil.rmtree(venv_path)

