import sys
from pathlib import Path

import packaging.version

from commons.command import run_command
from commons.common import Result, blog
from components.component import Component
from components.python_package import PythonPackageSet
from config import Config


class BlenderProgram(Component):
    """
    A class representing a Blender program with necessary information, including the Blender version, the Python
    version, and the Python packages.
    """

    # region Initialization
    is_renamable = True

    def __init__(self, blender_dir_abs_path: str or Path, name: str = None):
        """
        Initialize a BlenderProgram object based on an existing Blender directory.

        :param blender_dir_abs_path: a str or Path object of the Blender directory path, must be an absolute path
        :param name: a custom name for the Blender program from the user input
        """
        super().__init__(blender_dir_abs_path)
        self.dill_extension = Config.get_dill_extension(self)
        self.__class__.dill_extension = self.dill_extension
        self.if_store_in_repo = True
        self.init_params = {'blender_dir_path': blender_dir_abs_path, 'name': name}

    def create_instance(self) -> Result:
        """
        Create a BlenderProgram object based on an existing Blender directory path.

        :return: a Result object indicating if the initialization is successful, the message generated during the
                 initialization, and this object if successful.
        """

        def get_blender_exe_path() -> Path:
            """
            Get the Blender executable path based on the Blender directory path.

            :return: a Path object of the Blender executable path
            """
            if sys.platform == 'win32':
                blender_exe_path = Path(self.data_path) / 'blender.exe'
                if blender_exe_path.exists():
                    return blender_exe_path.relative_to(self.data_path)
                else:
                    raise FileNotFoundError(f'Blender executable file not found at {blender_exe_path}')
            else:
                raise NotImplementedError

        def get_blender_version() -> packaging.version.Version:
            """
            Get the Blender version by running a command in the terminal.

            :return: a Version object of the Blender version
            """
            result = run_command(f'"{self.data_path / self.blender_exe_path}" --version')
            if result.ok:
                stdout = result.data.stdout
                blender_version = stdout.split('\n')[0]
                if 'Blender' in blender_version:
                    return packaging.version.parse(blender_version.split(' ')[1])
            else:
                raise Exception(f'Error getting Blender version: {result.message}')

        def get_python_exe_path_version() -> (Path, packaging.version.Version):
            """
            Get the Python executable path and version of the Blender Python environment.

            :return: a tuple of Python executable path and Python version
            """
            result = run_command(f'"{self.data_path / self.blender_exe_path}" --background '
                                 f'--python-expr "import sys; print(\'interpreter_path:\', sys.executable); '
                                 f'print(\'version:\', sys.version)" --factory-startup --python-exit-code 1')
            if result.ok:
                stdout = result.data.stdout
                try:
                    python_exe_path = [line for line in stdout.split('\n')
                                       if line.startswith('interpreter_path:')][0].split(' ')[1]
                    python_version = [line for line in stdout.split('\n') if line.startswith('version:')][0].split(' ')[
                        1]
                    return Path(python_exe_path).relative_to(self.data_path), packaging.version.parse(python_version)
                except IndexError:
                    raise Exception(f'Error getting Blender Python exe path and version: {stdout}')
            else:
                raise Exception(f'Error getting Blender Python exe path and version: {result.message}')

        def get_python_site_packages_dir() -> Path:
            """
            Get the site package directory path of the Blender Python environment.

            :return: a Path object of the site package directory path
            """
            if sys.platform == 'win32':
                site_packages_dir = (self.data_path / self.python_exe_path).parent.parent / 'lib' / 'site-packages'
                if site_packages_dir.exists():
                    return site_packages_dir.relative_to(self.data_path)
                else:
                    raise FileNotFoundError(f'Blender Python site package directory not found at {site_packages_dir}')
            else:
                raise NotImplementedError

        def get_python_packages() -> PythonPackageSet:
            """
            Get the Python packages installed in Blender Python environment.

            :return: a PythonPackageSet object
            """
            result = run_command(f'"{self.data_path / self.python_exe_path}" -m pip freeze',
                                 expected_success_data_format=PythonPackageSet)
            if result.ok:
                return result.data
            else:
                raise Exception(f'Error getting Blender Python packages: {result.message}')

        if self.data_path is not None:
            try:
                # If no name is given, use the data path name
                self.name = self.init_params['name']
                if not self.name:
                    self.name = self.data_path.name
                self.blender_exe_path = get_blender_exe_path()
                if (self.data_path / self.blender_exe_path).exists():
                    self.blender_version = get_blender_version()
                    self.python_exe_path, self.python_version = get_python_exe_path_version()
                    self.python_site_pacakge_dir = get_python_site_packages_dir()
                    self.python_packages = get_python_packages()
                    return Result(True, f'Blender program instance created successfully.', self)
                else:
                    return Result(False, f'Blender executable file not found at {self.blender_exe_path}')
            except Exception as e:
                return Result(False, f'Error creating Blender program instance: {e}')
        else:
            return Result(False, f'Blender program directory not found at {self.data_path}')

    def verify(self) -> bool:
        """
        Verify if the Blender program is valid by checking if the Blender executable file exists and platform.

        :return: a boolean indicating if the Blender program is valid
        """
        return super().verify() and sys.platform == self.platform

    def __str__(self):
        return f'{self.__class__.__name__}: {self.name} ({self.blender_version})'


class BlenderProgramManager:

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def create(blender_dir_path: str or Path, name: str = None) -> Result:
        """
        Create a BlenderProgram object based on an existing Blender directory path that is external to the repository.

        :param blender_dir_path: a str or Path object of the Blender directory path, must be an absolute path
        :param name: a custom name for the Blender program from the user input

        :return: a Result object indicating if the initialization is successful, the message generated during the
                 initialization, and this BlenderProgram object if successful.
        """
        blog(2, f'Creating Blender program instance from {blender_dir_path}...')
        return BlenderProgram(blender_dir_path, name).create_instance()
