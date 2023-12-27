import os
import sys
from pathlib import Path

import virtualenv

from commons.common import Result as R
from commons.command import run_command
from components.blender_program import BlenderProgram
from components.manager import pooled_class
from components.python_package import PythonPackageSet


@pooled_class
class BlenderVenv:
    """
    A class representing a Blender virtual environment with necessary information, including a BlenderProgram object
    of its associated Blender (this venv originates from), and the Python packages.
    """

    def __init__(self, blender_venv_path):
        self.blender_venv_path = Path(blender_venv_path)
        if self.blender_venv_path.exists():
            self.blender_venv_config = self._get_blender_venv_config()
            self.blender_program = self._get_blender_program()
            self.python_packages = self._get_venv_packages()
        else:
            raise FileNotFoundError(f'Blender virtual environment not found at {self.blender_venv_path}')

    def _get_blender_venv_config(self) -> dict:
        """
        Get the Blender virtual environment config file's content as a dictionary.

        :return: a dictionary of the Blender virtual environment config file's content
        """
        cgf_path = self.blender_venv_path / 'pyvenv.cfg'
        if cgf_path.exists():
            cgf_dict = {}
            with open(cgf_path) as f:
                lines = f.readlines()
            for line in lines:
                if '=' in line:
                    cgf_dict[line.split('=')[0].strip()] = line.split('=')[1].strip()
            return cgf_dict
        else:
            raise FileNotFoundError(f'Blender virtual environment config file not found at {cgf_path}')

    def _get_blender_program(self) -> BlenderProgram:
        """
        Get the BlenderProgram object of the Blender (this venv originates from) based on the Blender virtual
        environment config file's base-executable path

        :return: a BlenderProgram object
        """
        if 'base-executable' in self.blender_venv_config:
            blender_python_path = Path(self.blender_venv_config['base-executable'])
            try:
                if sys.platform == 'win32':
                    blender_exe_path = blender_python_path.parent.parent.parent.parent / 'blender.exe'
                else:
                    raise NotImplementedError #  TODO: Implement for Linux and Mac, which may use different paths.
                blender_program = BlenderProgram(blender_exe_path)
                return blender_program
            except Exception as e:
                raise Exception(f'Error getting Blender program from Blender virtual environment config file: {e}')
        else:
            raise Exception(f'Error getting Blender program from Blender virtual environment config file: '
                            f'base-executable not found in {self.blender_venv_config}')

    def _get_venv_packages(self) -> PythonPackageSet:
        """
        Get the Python packages installed in the virtual environment.

        :return: a PythonPackageSet object
        """
        if sys.platform == "win32":
            activate_script = self.blender_venv_path / 'Scripts' / 'activate.bat'
            command = f'cmd.exe /c "{activate_script} && pip freeze"'
        else:
            activate_script = self.blender_venv_path / 'bin' / 'activate'
            command = f'source {activate_script} && pip freeze'
        result = run_command(command, expected_success_data_format=PythonPackageSet)
        if result.ok:
            return result.data
        else:
            raise Exception(f'Error getting virtual environment Python packages: {result.message}')

    def install_packages(self, env_path, packages: PythonPackageSet):
        if sys.platform == "win32":
            activate_script = env_path / 'Scripts' / 'activate.bat'
            command = f'cmd.exe /c "{activate_script} && pip install {packages.get_install_str()}"'
        else:
            activate_script = env_path / 'bin' / 'activate'
            command = f'source {activate_script} && pip install {packages.get_install_str()}'
        return run_command(command)


class BlenderVenvManager:
    """
    A static class for collecting managing Blender virtual environments related functions. This calss should not be
    instantiated.
    """

    def __new__(cls, *args, **kwargs):
        """Guard against instantiation"""
        raise Exception('BlenderVenvManager should not be instantiated.')

    @staticmethod
    def create_blender_venv(blender_program: BlenderProgram, venv_path: Path) -> BlenderVenv:
        """
        Create a Blender virtual environment at the given path from the given BlenderProgram object.

        :param blender_program: a BlenderProgram object
        :param venv_path: the path to create the Blender virtual environment

        :return: a BlenderVenv object
        """
        if blender_program.python_exe_path.exists():
            if not venv_path.exists():
                os.makedirs(venv_path)
                options = [venv_path.as_posix(), '--python', blender_program.python_exe_path.as_posix()]
                try:
                    virtualenv.cli_run(options)
                    return BlenderVenv(venv_path)
                except Exception as e:
                    raise Exception(f'Error creating Blender virtual environment: {e}')
            else:
                raise FileExistsError(f'Venv path already exists at {venv_path}')
        else:
            raise FileNotFoundError(f'Blender Python executable not found at {blender_program.python_exe_path}')
