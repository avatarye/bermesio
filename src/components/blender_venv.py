import os
from pathlib import Path
import sys
import shutil

import virtualenv

from commons.common import Result, Dillable, SharedFunctions as SF
from commons.command import run_command
from components.blender_program import BlenderProgram
from components.python_package import PythonLocalPackage, PythonPyPIPackage, PythonPackageSet
from components.python_dev_library import PythonDevLibrary
from config import Config


class BlenderVenv(Dillable):
    """
    A class representing a Blender virtual environment with necessary information, including a BlenderProgram object
    of its associated Blender (this venv originates from), and the Python packages.
    """

    # region Init

    # Site-packages directory in venv
    venv_site_packages_path = Path('Lib/site-packages')
    # bpy package directory in venv
    venv_bpy_package_path = Path('Lib/bpy_package')
    # Dev libraries directory in venv
    venv_dev_libraries_path = Path('Lib/dev_libraries')
    # Path for the pth file managed by this venv
    venv_managed_packages_pth_path = Path(f'Lib/site-packages/_{Config.app_name.lower()}_managed_packages.pth')

    def __init__(self, blender_venv_path):
        super().__init__()
        self.venv_path = Path(blender_venv_path)
        if self.venv_path.exists():
            self.name = self.venv_path.name
            self.venv_config: dict = self._get_blender_venv_config()
            self.blender_program: BlenderProgram = self._get_blender_program()
            self.site_packages: PythonPackageSet = self._get_site_packages()
            self.bpy_package: PythonLocalPackage = self._get_bpy_package()
        else:
            raise FileNotFoundError(f'Blender virtual environment not found at {self.venv_path}')

    def _get_blender_venv_config(self) -> dict:
        """
        Get the Blender virtual environment config file's content as a dictionary.

        :return: a dictionary of the Blender virtual environment config file's content
        """
        cgf_path = self.venv_path / 'pyvenv.cfg'
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
        if 'base-executable' in self.venv_config:
            blender_python_path = Path(self.venv_config['base-executable'])
            try:
                if sys.platform == 'win32':
                    blender_exe_path = blender_python_path.parent.parent.parent.parent / 'blender.exe'
                else:
                    raise NotImplementedError  # TODO: Implement for Linux and Mac, which may use different paths.
                blender_program = BlenderProgram(blender_exe_path)
                return blender_program
            except Exception as e:
                raise Exception(f'Error getting Blender program from Blender virtual environment config file: {e}')
        else:
            raise Exception(f'Error getting Blender program from Blender virtual environment config file: '
                            f'base-executable not found in {self.venv_config}')

    def _get_site_packages(self) -> PythonPackageSet:
        """
        Get the Python packages installed in the virtual environment.

        :return: a PythonPackageSet object
        """
        venv_package_path = self.venv_path / self.venv_site_packages_path
        return PythonPackageSet(venv_package_path) if venv_package_path.exists() else None

    def _get_bpy_package(self) -> PythonLocalPackage or None:
        """
        Get the bpy Python package installed in the virtual environment.

        :return: a PythonLocalPackage object or None if bpy is not installed
        """
        bpy_package_path = self.venv_path / self.venv_bpy_package_path / 'bpy'
        return PythonLocalPackage(bpy_package_path) if bpy_package_path.exists() else None

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
            activate_script = self.venv_path / 'Scripts' / 'activate.bat'
            no_deps_str = '--no-deps' if no_deps else ''
            if installation_path is not None:
                command = f'cmd.exe /c "{activate_script} && pip install {subject.get_installation_str()} ' \
                          f'{no_deps_str} --target {installation_path}"'
            else:
                command = (f'cmd.exe /c "{activate_script} && pip install {subject.get_installation_str()} '
                           f'{no_deps_str}"')
        else:
            raise NotImplementedError  # TODO: Implement for Linux and Mac, which may use different paths.
            # activate_script = self.venv_path / 'bin' / 'activate'
            # command = f'source {activate_script} && pip install {subject.get_installation_str()}'
        return run_command(command)

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
            installation_path = self.venv_path / self.venv_bpy_package_path
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

    def install_site_pacakge(self, subject: PythonPyPIPackage or PythonPackageSet) -> Result:
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
                return Result(False, f'Error getting site packages at {self.venv_path / self.venv_site_packages_path}')
            elif all([package_name in self.site_packages.package_dict for package_name in package_names]):
                return Result(True, f'Package(s) installed successfully')
            else:
                error_package_names = [package_name for package_name in package_names
                                       if package_name not in self.site_packages.package_dict]
                return Result(False, f'Error installing package(s) {error_package_names}')
        return result

    def install_dev_library(self, subject: PythonDevLibrary) -> Result:
        """
        Install the given PythonDevLibrary object in the virtual environment's dev library dir.

        :param subject: a PythonDevLibrary object

        :return: a Result object
        """
        if subject.verify():
            result = subject.deploy(self.venv_path / self.venv_dev_libraries_path)
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
            line_to_write = (f'import sys; sys.path.append(sys.prefix + "\\{package_path.as_posix()}")  '
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
        pth_path = self.venv_path / self.venv_managed_packages_pth_path
        return self._add_package_dir_to_pth_file(pth_path, self.venv_bpy_package_path)

    def add_bpy_package_to_blender_pth(self) -> Result:
        """
        Add a line to the associated Blender's pth file to append the bpy package path to the Blender's sys.path. This
        is only needed for special development purposes, where a process uses Blender's Python interpreter to run some
        python code that has dependencies on bpy package.

        :return: a Result object
        """
        pth_path = self.blender_program.python_site_pacakge_dir / self.venv_managed_packages_pth_path.name
        return self._add_package_dir_to_pth_file(pth_path, self.venv_path / self.venv_bpy_package_path)

    def add_site_packages_to_blender_pth(self) -> Result:
        """
        Add a line to the associated Blender's pth file to append the site-package path to Blender's sys.path.

        :return: a Result object
        """
        pth_path = self.blender_program.python_site_pacakge_dir / self.venv_managed_packages_pth_path.name
        return self._add_package_dir_to_pth_file(pth_path, self.venv_path / self.venv_site_packages_path)

    def add_dev_libraries_to_venv_pth(self) -> Result:
        """
        Add a line to the venv pth file to append the dev libraries path to this venv's sys.path.

        :return: a Result object
        """
        pth_path = self.venv_path / self.venv_managed_packages_pth_path
        return self._add_package_dir_to_pth_file(pth_path, self.venv_dev_libraries_path)

    def add_dev_libraries_to_blender_pth(self) -> Result:
        """
        Add a line to the associated Blender's pth file to append the dev libraries path to Blender's sys.path.

        :return: a Result object
        """
        pth_path = self.blender_program.python_site_pacakge_dir / self.venv_managed_packages_pth_path.name
        return self._add_package_dir_to_pth_file(pth_path, self.venv_path / self.venv_dev_libraries_path)

    def remove_venv_pth(self) -> Result:
        """
        Remove the venv pth file.

        :return: a Result object
        """
        return SF.remove_target_path(self.venv_path / self.venv_managed_packages_pth_path)

    def remove_blender_pth(self) -> Result:
        """
        Remove the associated Blender's pth file.

        :return: a Result object
        """
        return SF.remove_target_path(self.blender_program.python_site_pacakge_dir /
                                     self.venv_managed_packages_pth_path.name)

    # endregion

    def verify(self) -> bool:
        """
        Verify if the Blender virtual environment is valid. This is often called after restored from a dilled object.

        :return: True if the Blender virtual environment is valid, otherwise False
        """
        return self.venv_path.exists() and self.blender_program.verify()

    def __str__(self):
        return f'BlenderVenv: {self.name} ({self.blender_program})'

    def __eq__(self, other: 'BlenderVenv'):
        """
        The equality of 2 BlenderVenv objects is determined by the addon path instead of the instance itself. If the
        instance equality is required, use compare_uuid() from Dillable class.

        :param other: another BlenderVenv object

        :return: True if the Blender venv path of this instance is the same as the other instance, otherwise False
        """
        if issubclass(other.__class__, BlenderVenv):
            return self.venv_path == other.venv_path
        return False

    def __hash__(self):
        return hash(self.venv_path.as_posix())


class BlenderVenvManager:
    """
    A static class for collecting managing Blender virtual environments related functions fall outside the scope of the
    BlenderVenv class.
    """

    def __new__(cls, *args, **kwargs):
        raise Exception('BlenderVenvManager should not be instantiated.')

    @staticmethod
    def create_blender_venv(blender_program: BlenderProgram, venv_path: str or Path, delete_existing=False) -> Result:
        """
        Create a Blender virtual environment at the given path from the given BlenderProgram object.

        :param blender_program: a BlenderProgram object
        :param venv_path: the path to create the Blender virtual environment
        :param delete_existing: whether to delete the existing directory at the given path

        :return: a Result object with the BlenderVenv object as the data
        """
        venv_path = Path(venv_path)
        result = SF.ready_target_path(venv_path, ensure_parent_dir=True, delete_existing=delete_existing)
        if not result:
            return result
        if blender_program.verify():
            try:
                os.makedirs(venv_path)
                options = [venv_path.as_posix(), '--python', blender_program.python_exe_path.as_posix()]
                virtualenv.cli_run(options)
                blender_venv = BlenderVenv(venv_path)
                if blender_venv.verify():
                    return Result(True, 'Blender virtual environment created successfully', blender_venv)
                else:
                    return Result(False, f'Error creating Blender virtual environment: {venv_path}')
            except Exception as e:
                return Result(False, f'Error creating Blender virtual environment: {e}')
        else:
            return Result(False, f'Error creating Blender virtual environment: Blender program not verified')
