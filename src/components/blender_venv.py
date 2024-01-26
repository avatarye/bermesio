import os
from pathlib import Path
import sys
import shutil

import virtualenv

from commons.common import Result, blog, SharedFunctions as SF
from commons.command import run_command
from components.blender_program import BlenderProgram, BlenderProgramManager
from components.component import Component, Dillable
from components.python_package import PythonLocalPackage, PythonPyPIPackage, PythonPackageSet
from components.python_dev_library import PythonDevLibrary
from config import Config


class BlenderVenv(Component):
    """
    A class representing a Blender virtual environment with necessary information, including a BlenderProgram object
    of its associated Blender (this venv originates from), and the Python packages.
    """

    # region Init
    
    is_editable = True

    # Site-packages directory in venv
    venv_site_packages_path = Path('Lib/site-packages')
    # bpy package directory in venv
    venv_bpy_package_path = Path('Lib/bpy_package')
    # Dev libraries directory in venv
    venv_dev_libraries_path = Path('Lib/dev_libraries')
    # Path for the pth file managed by this venv
    venv_managed_packages_pth_path = Path(f'Lib/site-packages/_{Config.app_name.lower()}_managed_packages.pth')

    def __init__(self, blender_venv_abs_path: str or Path, name: str = None):
        """
        Initialize a BlenderVenv object based on an existing Blender virtual environment directory.

        :param blender_venv_abs_path: a str or Path object of the Blender virtual environment directory path, must be
                                      an absolute path
        :param name: a custom name for the Blender virtual environment from the user input
        """
        super().__init__(blender_venv_abs_path)
        self.dill_extension = Config.get_dill_extension(self)
        self.__class__.dill_extension = self.dill_extension
        # All BlenderVenv instances must be created in the repo directly. No need to store it.
        self.if_store_in_repo = False
        self.init_params = {'blender_venv_path': blender_venv_abs_path, 'name': name}

    def _get_site_packages(self) -> PythonPackageSet:
        """
        Get the Python packages installed in the virtual environment.

        :return: a PythonPackageSet object
        """
        venv_package_path = self.data_path / self.venv_site_packages_path
        return PythonPackageSet(venv_package_path) if venv_package_path.exists() else None

    def _get_bpy_package(self) -> PythonLocalPackage or None:
        """
        Get the bpy Python package installed in the virtual environment.

        :return: a PythonLocalPackage object or None if bpy is not installed
        """
        bpy_package_path = self.data_path / self.venv_bpy_package_path / 'bpy'
        return PythonLocalPackage(bpy_package_path) if bpy_package_path.exists() else None

    def create_instance(self) -> Result:
        """
        Create a BlenderVenv object based on an existing Blender venv directory path. Please note that this method
        does not create a Blender venv, it only creates the BlenderVenv object.

        :return: a Result object indicating if the initialization is successful, the message generated during the
                 initialization, and this object if successful.
        """

        def get_blender_venv_config() -> dict:
            """
            Get the Blender virtual environment config file's content as a dictionary.

            :return: a dictionary of the Blender virtual environment config file's content
            """
            cgf_path = self.data_path / 'pyvenv.cfg'
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

        def get_blender_program() -> BlenderProgram:
            """
            Get the BlenderProgram object of the Blender (this venv originates from) based on the Blender virtual
            environment config file's base-executable path

            :return: a BlenderProgram object
            """
            if 'base-executable' in self.venv_config:
                blender_python_path = Path(self.venv_config['base-executable'])
                try:
                    if sys.platform == 'win32':
                        blender_dir_path = blender_python_path.parent.parent.parent.parent
                    else:
                        raise NotImplementedError  # TODO: Implement for Linux and Mac, which may use different paths.
                    result = BlenderProgramManager.create(blender_dir_path)
                    if result:
                        return result.data
                    else:
                        raise Exception(f'Error getting Blender program from Blender virtual environment config file: '
                                        f'{result.message}')
                except Exception as e:
                    raise Exception(f'Error getting Blender program from Blender virtual environment config file: {e}')
            else:
                raise Exception(f'Error getting Blender program from Blender virtual environment config file: '
                                f'base-executable not found in {self.venv_config}')

        if self.data_path.exists():
            if Config.repo_dir in self.data_path.parents:  # Ensure this venv is located in the repo
                try:
                    # If no name is given, use the data path name
                    self.name = self.init_params['name']
                    if not self.name:
                        self.name = self.data_path.name
                    self.venv_config: dict = get_blender_venv_config()
                    self.blender_program: BlenderProgram = get_blender_program()
                    self.site_packages: PythonPackageSet = self._get_site_packages()
                    self.bpy_package: PythonLocalPackage = self._get_bpy_package()
                    return Result(True, '', self)
                except Exception as e:
                    return Result(False, f'Error creating Blender virtual environment: {e}')
            else:
                return Result(False, f'Blender virtual environment not in repository: {self.data_path}')
        else:
            return Result(False, f'Blender virtual environment directory not found at {self.data_path}')

    def store_in_repo(self, repo_dir: str or Path) -> Result:
        """BlenderVenv shouldn't be stored in repo, but created from a BlenderProgram in the repo directly."""
        raise NotImplementedError

    # endregion

    # region Configure venv

    def _install_packages(self, subject: PythonPyPIPackage or PythonPackageSet, no_deps: bool = False,
                          installation_path: Path = None) -> Result:
        """
        Install the given PythonPyPIPackage or PythonPackageSet object in the virtual environment.

        :param subject: a PythonPyPIPackage or PythonPackageSet object
        :param no_deps: a flag indicating whether to install the dependencies of the given package(s)
        :param installation_path: a Path object of the installation path, if None, install to the virtual environment

        :return: a Result object
        """
        if sys.platform == "win32":
            activate_script = self.data_path / 'Scripts' / 'activate.bat'
            no_deps_str = '--no-deps' if no_deps else ''
            if installation_path is not None:
                command = f'cmd.exe /c "{activate_script} && pip install {subject.get_installation_str()} ' \
                          f'{no_deps_str} --target {installation_path}"'
            else:
                command = (f'cmd.exe /c "{activate_script} && pip install {subject.get_installation_str()} '
                           f'{no_deps_str}"')
        else:
            raise NotImplementedError  # TODO: Implement for Linux and Mac, which may use different paths.
            # activate_script = self.data_path / 'bin' / 'activate'
            # command = f'source {activate_script} && pip install {subject.get_installation_str()}'
        return run_command(command)

    @Dillable.save_dill
    def install_bpy_package(self, force: bool = False) -> Result:
        """
        Install the bpy package in a dedicated path in the virtual environment. This is to avoid the bpy package being
        installed in the site-packages directory, which may cause conflicts with Blender's own Python environment.

        :param force: a flag indicating whether to force install the bpy package

        :return: a Result object
        """
        # Check if bpy package is already installed
        self.bpy_package = self._get_bpy_package()
        if self.bpy_package is None or force:
            installation_path = self.data_path / self.venv_bpy_package_path
            # If force is True, remove the bpy package if it exists
            if force and installation_path.exists():
                shutil.rmtree(installation_path / 'bpy')
                if (installation_path / 'bpy').exists():
                    return Result(False, f'Error removing bpy package at {installation_path / "bpy"}')
            # Install bpy package with dependencies.
            result = self._install_packages(PythonPyPIPackage('bpy'), installation_path=installation_path)
            if result.ok:
                self.bpy_package = self._get_bpy_package()
                if self.bpy_package is None:
                    return Result(False, f'Error installing bpy package at {installation_path / "bpy"}')
            return result
        else:
            return Result(True, 'bpy package already installed')

    @Dillable.save_dill
    def install_site_package(self, subject: PythonPyPIPackage or PythonPackageSet) -> Result:
        """
        Install the given PythonPyPIPackage or PythonPackageSet object in the virtual environment's site-packages dir.

        :param subject: a PythonPyPIPackage or PythonPackageSet object

        :return: a Result object
        """
        # Install the package(s) with dependencies.
        result = self._install_packages(subject)
        if result.ok:
            self.site_packages = self._get_site_packages()
            package_names = [subject.name] if isinstance(subject, PythonPyPIPackage) else subject.package_dict.keys()
            # Check if the package(s) is installed successfully.
            if self.site_packages is None:
                return Result(False, f'Error getting site packages at {self.data_path / self.venv_site_packages_path}')
            elif all([package_name in self.site_packages.package_dict for package_name in package_names]):
                return Result(True, f'Package(s) installed successfully')
            else:
                error_package_names = [package_name for package_name in package_names
                                       if package_name not in self.site_packages.package_dict]
                return Result(False, f'Error installing package(s) {error_package_names}')
        return result

    @Dillable.save_dill
    def install_dev_library(self, subject: PythonDevLibrary) -> Result:
        """
        Install the given PythonDevLibrary object in the virtual environment's dev library dir.

        :param subject: a PythonDevLibrary object

        :return: a Result object
        """
        if subject.verify():
            result = subject.deploy(self.data_path / self.venv_dev_libraries_path)
            return result
        else:
            return Result(False, f'The development library {subject.name} is not valid')

    @staticmethod
    def _add_package_dir_to_pth_file(pth_path: Path, package_path: Path) -> Result:
        """
        Add a line to the given pth file to append the given package path to sys.path. This can be used to append the
        input package to the target Python environment's sys.path.

        :param pth_path: a Path object of the pth file
        :param package_path: a Path object of the package path to be appended to sys.path

        :return: a Result object
        """
        lines = []
        line_indicator = f'# venv_managed_path: {package_path.name}'
        if package_path.is_absolute():
            line_to_write = f'import sys; sys.path.append("{package_path.as_posix()}")  {line_indicator}\n'
        else:
            line_to_write = (f'import sys; sys.path.append(sys.prefix + "{os.sep}{package_path.as_posix()}")  '
                             f'{line_indicator}\n')
        if pth_path.exists():
            with open(pth_path, 'r') as f:
                lines = f.readlines()
            lines = [line for line in lines if line_indicator not in line]
        lines.append(line_to_write)
        with open(pth_path, 'w') as f:
            f.writelines(lines)
        return Result(True, f'Line "{line_to_write}" written to {pth_path}')

    def add_bpy_package_to_venv_pth(self) -> Result:
        """
        Add a line to the venv pth file to append the bpy package path to this venv's sys.path.

        :return: a Result object
        """
        pth_path = self.data_path / self.venv_managed_packages_pth_path
        return self._add_package_dir_to_pth_file(pth_path, self.venv_bpy_package_path)

    def add_dev_libraries_to_venv_pth(self) -> Result:
        """
        Add a line to the venv pth file to append the dev libraries path to this venv's sys.path.

        :return: a Result object
        """
        pth_path = self.data_path / self.venv_managed_packages_pth_path
        return self._add_package_dir_to_pth_file(pth_path, self.data_path / self.venv_dev_libraries_path)

    def add_bpy_package_to_blender_pth(self) -> Result:
        """
        Add a line to the associated Blender's pth file to append the bpy package path to the Blender's sys.path. This
        is only needed for special development purposes, where a process uses Blender's Python interpreter to run some
        python code that has dependencies on bpy package.

        :return: a Result object
        """
        pth_path = (self.blender_program.data_path / self.blender_program.python_site_pacakge_dir /
                    self.venv_managed_packages_pth_path.name)
        return self._add_package_dir_to_pth_file(pth_path, self.data_path / self.venv_bpy_package_path)

    def add_site_packages_to_blender_pth(self) -> Result:
        """
        Add a line to the associated Blender's pth file to append the site-package path to Blender's sys.path.

        :return: a Result object
        """
        pth_path = (self.blender_program.data_path / self.blender_program.python_site_pacakge_dir /
                    self.venv_managed_packages_pth_path.name)
        return self._add_package_dir_to_pth_file(pth_path, self.data_path / self.venv_site_packages_path)

    def add_dev_libraries_to_blender_pth(self) -> Result:
        """
        Add a line to the associated Blender's pth file to append the dev libraries path to Blender's sys.path.

        :return: a Result object
        """
        pth_path = (self.blender_program.data_path / self.blender_program.python_site_pacakge_dir /
                    self.venv_managed_packages_pth_path.name)
        return self._add_package_dir_to_pth_file(pth_path, self.data_path / self.venv_dev_libraries_path)

    def remove_venv_pth(self) -> Result:
        """
        Remove the venv pth file.

        :return: a Result object
        """
        return SF.remove_target_path(self.data_path / self.venv_managed_packages_pth_path)

    def remove_blender_pth(self) -> Result:
        """
        Remove the associated Blender's pth file.

        :return: a Result object
        """
        return SF.remove_target_path(self.blender_program.data_path / self.blender_program.python_site_pacakge_dir /
                                     self.venv_managed_packages_pth_path.name)

    # endregion

    def get_activate_script_path(self) -> Path or None:
        """
        Get the activate script path of the virtual environment.

        :return: a Path object of the activate script path
        """
        if sys.platform == "win32":
            activate_script = self.data_path / 'Scripts' / 'activate.bat'
            if activate_script.exists():
                return activate_script
        else:
            raise NotImplementedError
        return

    def _get_status_dict(self) -> dict:
        """
        Get the status dictionary of this BlenderVenv object, including the presence of the bpy package and dev libs.
        This is used for the GUI to display the status of the Blender virtual environment.

        :return: a dictionary of the status
        """
        site_package_names, dev_library_names = [], {}
        if (self.data_path / self.venv_dev_libraries_path).exists():
            dev_library_names =  [p.name for p in (self.data_path / self.venv_dev_libraries_path).iterdir()]
        if self.site_packages is not None:
            site_package_names = self.site_packages.package_dict.keys()
        return {'site_packages': site_package_names,
                'has_bpy_package': self.bpy_package is not None,
                'dev_libraries': dev_library_names}

    def verify(self) -> bool:
        """
        Verify if the Blender virtual environment is valid. It is valid if the BlenderProgram object is valid and the
        Blender virtual environment directory exists and the platform is the same as the current platform.

        :return: True if the Blender virtual environment is valid, otherwise False
        """
        # TODO: Add a verification on the hard-coded original Python interpreter path in the activation scripts to guard
        #       against the case where the repo moved to another location resulting in the associated BlenderProgram's
        #       Python cannot be found.
        return super().verify() and self.blender_program.verify() and sys.platform == self.platform

    def __str__(self):
        return f'{self.__class__.__name__}: {self.name} ({self.blender_program})'


class BlenderVenvManager:
    """
    A static class for collecting managing Blender virtual environments related functions fall outside the scope of the
    BlenderVenv class.
    """

    def __new__(cls, *args, **kwargs):
        raise Exception('BlenderVenvManager should not be instantiated.')

    @staticmethod
    def create_venv_from_blender_program(blender_program: BlenderProgram, blender_venv_abs_path: str or Path,
                                         name: str = None) -> Result:
        """
        Physically create a virtual environment at the given path based on the Python interpreter of the given
        BlenderProgram object.

        :param blender_program: a BlenderProgram object
        :param blender_venv_abs_path: the path to create the Blender virtual environment
        :param name: a custom name for the Blender virtual environment from the user input

        :return: a Result object with the BlenderVenv object as the data
        """
        blender_venv_abs_path = Path(blender_venv_abs_path)
        # Ensure the venv path is in the repo
        if Config.repo_dir in blender_venv_abs_path.parents:
            result = SF.ready_target_path(blender_venv_abs_path, ensure_parent_dir=True)
            if not result:
                return result
            if blender_program.verify():
                try:
                    os.makedirs(blender_venv_abs_path)
                    blender_python_exe_path = blender_program.data_path / blender_program.python_exe_path
                    options = [blender_venv_abs_path.as_posix(), '--python', blender_python_exe_path.as_posix()]
                    virtualenv.cli_run(options)
                    if blender_venv_abs_path.exists():
                        return BlenderVenvManager.create(blender_venv_abs_path, name=name)
                    else:
                        return Result(False, f'Error creating Blender virtual environment at {blender_venv_abs_path}')
                except Exception as e:
                    return Result(False, f'Error creating Blender virtual environment: {e}')
            else:
                return Result(False, f'Error creating Blender virtual environment: Blender program not verified')
        else:
            return Result(False, f'Error creating Blender virtual environment: not in the repository')

    @staticmethod
    def create(blender_venv_abs_path: str or Path, name: str =None) -> Result:
        """
        Create a Blender venv instance from a pre-existing virtual environment created from a Blender's Python
        interpreter. Typically, the venv path is from the repository's venv directory.

        :param blender_venv_abs_path: the path to create the Blender virtual environment
        :param name: a custom name for the Blender virtual environment from the user input

        :return:a Result object indicating if the initialization is successful, the message generated during the
                initialization, and this BlenderProgram object if successful.
        """
        blender_venv_abs_path = Path(blender_venv_abs_path)
        # Ensure the venv path is in the repo
        if Config.repo_dir in blender_venv_abs_path.parents:
            blog(2, f'Creating a Blender virtual environment from {blender_venv_abs_path}...')
            return BlenderVenv(blender_venv_abs_path, name=name).create_instance()
        else:
            return Result(False, f'Error creating Blender virtual environment: not in the repository')
