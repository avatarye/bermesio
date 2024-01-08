from pathlib import Path

from components.python_package import PythonPyPIPackage
from components.blender_program import BlenderProgram
from components.blender_venv import BlenderVenvManager


def create_venv(blender_path, venv_path):
    blender_program = BlenderProgram(blender_path)
    blender_venv = BlenderVenvManager.create_venv_from_blender_program(blender_program, venv_path, delete_existing=True)
    blender_venv.install_bpy_package()
    blender_venv.install_site_pacakge(PythonPyPIPackage('pyautogen'))

def create_blender_setup():
    creation_dict = {

    }

def create_repo():
    creation_dict = {
    }

if __name__ == '__main__':
    blender_path = Path(r'c:\TechDepot\AvatarTools\Blender\Launcher\stable\blender-3.6.7-windows-x64\blender.exe')
    venv_path = Path(r'c:\TechDepot\Github\bermesio\_data\venvs\venv_blender_3.6.7_GUI')
    create_venv(blender_path, venv_path)