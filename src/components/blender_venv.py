import datetime
import os
from pathlib import Path
import sys
import shutil

import virtualenv

from commons.common import Result, Dillable, SharedFunctions as SF
from commons.command import run_command
from components.blender_program import BlenderProgram
from components.manager import pooled_class
from components.python_package import PythonLocalPackage, PythonPyPIPackage, PythonLibrary, PythonPackageSet
from config import Config


@pooled_class
class BlenderVenv(Dillable):
    """
    A class representing a Blender virtual environment with necessary information, including a BlenderProgram object
    of its associated Blender (this venv originates from), and the Python packages.
    """

    venv_site_packages_path = Path('Lib/site-packages')
    venv_bpy_package_path = Path('Lib/bpy_package')
    venv_local_libraries_paths = [Path('Lib/local_libs')]
    venv_managed_packages_pth_path = Path(f'Lib/site-packages/_{Config.app_name.lower()}_managed_packages.pth')

    def __init__(self, blender_venv_path):
        super().__init__()
        self.venv_path = Path(blender_venv_path)
        if self.venv_path.exists():
            self.venv_config = self._get_blender_venv_config()
            self.blender_program = self._get_blender_program()
            self.site_packages = self._get_site_packages()
            self.local_libraries = self._get_local_libraries()
            self.bpy_package = self._get_bpy_package()
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

    def _get_local_libraries(self) -> PythonPackageSet:
        return None

    def _get_bpy_package(self) -> PythonLocalPackage or None:
        """
        Get the bpy Python package installed in the virtual environment.

        :return: a PythonLocalPackage object or None if bpy is not installed
        """
        bpy_package_path = self.venv_path / self.venv_bpy_package_path / 'bpy'
        return PythonLocalPackage(bpy_package_path) if bpy_package_path.exists() else None

    def _install_packages(self, subject: PythonPyPIPackage or PythonPackageSet, no_deps=False,
                          installation_path=None) -> Result:
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

    def install_bpy_package(self, force=False) -> Result:
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

    def _add_package_pth_file(self, pth_path: Path, package_path: Path) -> Result:
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
            lines = [l for l in lines if line_indicator not in l]
        lines.append(line_to_write)
        with open(pth_path, 'w') as f:
            f.writelines(lines)
        return Result(True, f'Line "{line_to_write}" written to {pth_path}')

    def add_bpy_package_to_venv_pth(self) -> Result:
        pth_path = self.venv_path / self.venv_managed_packages_pth_path
        return self._add_package_pth_file(pth_path, self.venv_bpy_package_path)

    def add_bpy_package_to_blender_pth(self) -> Result:
        pth_path = self.blender_program.python_site_pacakge_dir / self.venv_managed_packages_pth_path.name
        return self._add_package_pth_file(pth_path, self.venv_path / self.venv_bpy_package_path)

    def add_site_packages_to_blender_pth(self) -> Result:
        pth_path = self.blender_program.python_site_pacakge_dir / self.venv_managed_packages_pth_path.name
        return self._add_package_pth_file(pth_path, self.venv_path / self.venv_site_packages_path)

    def _add_local_libraries_to_pth(self, pth_path: Path) -> Result:
        results = []
        for local_library_path in self.venv_local_libraries_paths:
            results.append(self._add_package_pth_file(pth_path, local_library_path))
        if all([result.ok for result in results]):
            return Result(True, f'Local libraries paths added to {self.venv_managed_packages_pth_path}')
        else:
            return Result(False, f'Error adding local libraries paths to {self.venv_managed_packages_pth_path}')

    def add_local_libraries_to_venv_pth(self) -> Result:
        pth_path = self.venv_path / self.venv_managed_packages_pth_path
        return self._add_local_libraries_to_pth(pth_path)

    def add_local_libraries_to_blender_pth(self) -> Result:
        pth_path = self.blender_program.python_site_pacakge_dir / self.venv_managed_packages_pth_path.name
        return self._add_local_libraries_to_pth(pth_path)

    def remove_venv_pth(self) -> Result:
        return SF.remove_file(self.venv_path / self.venv_managed_packages_pth_path)

    def remove_blender_pth(self) -> Result:
        return SF.remove_file(self.blender_program.python_site_pacakge_dir / self.venv_managed_packages_pth_path.name)

    def verify(self) -> bool:
        """
        Verify if the Blender virtual environment is valid. This is often called after restored from a dilled object.

        :return: True if the Blender virtual environment is valid, otherwise False
        """
        return self.venv_path.exists() and self.blender_program.verify()

    def __str__(self):
        return f'Venv: {self.venv_path.name} ({self.blender_program})'


class BlenderVenvManager:
    """
    A static class for collecting managing Blender virtual environments related functions. This class should not be
    instantiated.
    """

    def __new__(cls, *args, **kwargs):
        """Guard against instantiation"""
        raise Exception('BlenderVenvManager should not be instantiated.')

    @staticmethod
    def create_blender_venv(blender_program: BlenderProgram, venv_path: str or Path,
                            delete_existing=False) -> BlenderVenv:
        """
        Create a Blender virtual environment at the given path from the given BlenderProgram object.

        :param blender_program: a BlenderProgram object
        :param venv_path: the path to create the Blender virtual environment
        :param delete_existing: whether to delete the existing directory at the given path

        :return: a BlenderVenv object
        """
        venv_path = Path(venv_path)
        SF.ready_target_path(venv_path, ensure_parent_dir=True, delete_existing=delete_existing)
        if blender_program.verify():
            os.makedirs(venv_path)
            options = [venv_path.as_posix(), '--python', blender_program.python_exe_path.as_posix()]
            try:
                virtualenv.cli_run(options)
                return BlenderVenv(venv_path)
            except Exception as e:
                raise Exception(f'Error creating Blender virtual environment: {e}')
        else:
            raise FileNotFoundError(f'Blender Python executable not found at {blender_program.python_exe_path}')
