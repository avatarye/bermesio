import datetime
import sys
from pathlib import Path

import packaging.version

from commons.command import run_command
from commons.common import Dillable
from components.manager import pooled_class
from components.python_package import PythonPackageSet


# @pooled_class
class BlenderProgram(Dillable):
    """
    A class representing a Blender program with necessary information, including the Blender version, the Python
    version, and the Python packages.
    """
    def __init__(self, blender_exe_path, name=None):
        super().__init__()
        self.blender_exe_path = Path(blender_exe_path)
        if self.blender_exe_path.exists():
            self.blender_version = self._get_blender_version()
            self.blender_dir = self._get_blender_dir()
            self.python_exe_path, self.python_version = self._get_python_exe_path_version()
            self.python_site_pacakge_dir = self._get_python_site_package_dir()
            self.python_packages = self._get_python_packages()
            # If no name is given, use the default name
            if not name:
                self.name = f'Blender_{self.blender_version}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
            else:
                self.name = name
        else:
            raise FileNotFoundError(f'Blender executable not found at {self.blender_exe_path}')

    def _get_blender_version(self) -> packaging.version.Version:
        result = run_command(f'"{self.blender_exe_path}" --version')
        if result.ok:
            stdout = result.data.stdout
            blender_version = stdout.split('\n')[0]
            if 'Blender' in blender_version:
                return packaging.version.parse(blender_version.split(' ')[1])
        else:
            raise Exception(f'Error getting Blender version: {result.message}')

    def _get_blender_dir(self) -> Path:
        """
        Get the Blender directory path based on the Blender executable path.

        :return: a Path object of the Blender directory path
        """
        if sys.platform == 'win32':
            return self.blender_exe_path.parent
        else:
            raise NotImplementedError

    def _get_python_exe_path_version(self) -> (Path, packaging.version.Version):
        """
        Get the Python executable path and version of the Blender Python environment.

        :return: a tuple of Python executable path and Python version
        """
        result = run_command(f'"{self.blender_exe_path}" --background '
                             f'--python-expr "import sys; print(\'interpreter_path:\', sys.executable); '
                             f'print(\'version:\', sys.version)" --factory-startup --python-exit-code 1')
        if result.ok:
            stdout = result.data.stdout
            try:
                python_exe_path = [line for line in stdout.split('\n')
                                   if line.startswith('interpreter_path:')][0].split(' ')[1]
                python_version = [line for line in stdout.split('\n') if line.startswith('version:')][0].split(' ')[1]
                return Path(python_exe_path), packaging.version.parse(python_version)
            except IndexError:
                raise Exception(f'Error getting Blender Python exe path and version.')
        else:
            raise Exception(f'Error getting Blender Python exe path and version: {result.message}')

    def _get_python_site_package_dir(self) -> Path:
        """
        Get the site package directory path of the Blender Python environment.

        :return: a Path object of the site package directory path
        """
        if sys.platform == 'win32':
            return self.python_exe_path.parent.parent / 'lib' / 'site-packages'
        else:
            raise NotImplementedError

    def _get_python_packages(self) -> PythonPackageSet:
        """
        Get the Python packages installed in Blender Python environment.

        :return: a PythonPackageSet object
        """
        result = run_command(f'"{self.python_exe_path}" -m pip freeze',
                             expected_success_data_format=PythonPackageSet)
        if result.ok:
            return result.data
        else:
            raise Exception(f'Error getting Blender Python packages: {result.message}')

    def verify(self) -> bool:
        """
        Verify if the Blender executable is valid. This is often called after restored from a dilled object.

        :return: True if the Blender executable is valid, otherwise False
        """
        return self.blender_exe_path.exists() and self.python_exe_path.exists()

    def __str__(self):
        return f'Blender: {self.name} ({self.blender_version})'
