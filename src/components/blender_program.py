from pathlib import Path

import packaging.version

from commons.command import run_command
from components.python_package import PythonPackageSet


class BlenderProgram:
    """
    A class representing a Blender program with necessary information, including the Blender version, the Python
    version, and the Python packages.
    """

    def __init__(self, blender_exe_path):
        self.blender_exe_path = Path(blender_exe_path)
        if self.blender_exe_path.exists():
            self.blender_version = self._get_blender_version()
            self.python_exe_path, self.python_version = self._get_python_exe_path_version()
            self.python_packages = self._get_python_packages()
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

    def _get_python_exe_path_version(self):
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

    def _get_python_packages(self):
        result = run_command(f'"{self.python_exe_path}" -m pip freeze',
                             expected_success_data_format=PythonPackageSet)
        if result.ok:
            return result.data
        else:
            raise Exception(f'Error getting Blender Python packages: {result.message}')
