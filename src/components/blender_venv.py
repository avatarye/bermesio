import os
from pathlib import Path
import sys
import shutil
import subprocess

import virtualenv

from commons.common import Result as R, blog
from commons.command import run_command
from components.blender_program import BlenderProgram
from components.manager import pooled_class
from components.python_package import PythonLocalPackage, PythonPyPIPackage, PythonLibrary, PythonPackageSet


@pooled_class
class BlenderVenv:
    """
    A class representing a Blender virtual environment with necessary information, including a BlenderProgram object
    of its associated Blender (this venv originates from), and the Python packages.
    """

    venv_site_packages_path = Path('Lib/site-packages')
    venv_bpy_package_path = Path('Lib/bpy_package')
    venv_local_libraries_path = Path('Lib/local_libs')

    def __init__(self, blender_venv_path):
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
                          installation_path=None) -> R:
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

    def install_bpy_package(self, force=False) -> R:
        # Check if bpy package is already installed
        self.bpy_package = self._get_bpy_package()
        if self.bpy_package is None or force:
            installation_path = self.venv_path / self.venv_bpy_package_path
            # If force is True, remove the bpy package if it exists
            if force and installation_path.exists():
                shutil.rmtree(installation_path / 'bpy')
                if (installation_path / 'bpy').exists():
                    return R(False, f'Error removing bpy package at {installation_path / "bpy"}')
            # Install bpy package with dependencies.
            result = self._install_packages(PythonPyPIPackage('bpy'), installation_path=installation_path)
            if result.ok:
                self.bpy_package = self._get_bpy_package()
                if self.bpy_package is None:
                    return R(False, f'Error installing bpy package at {installation_path / "bpy"}')
            return result
        else:
            return R(True, 'bpy package already installed')

    def install_site_pacakge(self, subject: PythonPyPIPackage or PythonPackageSet) -> R:
        # Install the package(s) with dependencies.
        result = self._install_packages(subject)
        if result.ok:
            self.site_packages = self._get_site_packages()
            package_names = [subject.name] if isinstance(subject, PythonPyPIPackage) else subject.package_dict.keys()
            # Check if the package(s) is installed successfully.
            if self.site_packages is None:
                return R(False, f'Error getting site packages at {self.venv_path / self.venv_site_packages_path}')
            elif all([package_name in self.site_packages.package_dict for package_name in package_names]):
                return R(True, f'Package(s) installed successfully')
            else:
                error_package_names = [package_name for package_name in package_names
                                       if package_name not in self.site_packages.package_dict]
                return R(False, f'Error installing package(s) {error_package_names}')
        return result

    def launch_shell(self, add_local_libs=True, add_bpy_path=True):
        if add_local_libs:
            local_libs_path = self.venv_path / self.venv_local_libraries_path
            os.environ['PYTHONPATH'] += ';' + local_libs_path.as_posix()
        if add_bpy_path:
            local_bpy_package_path = self.venv_path / self.venv_bpy_package_path
            os.environ['PYTHONPATH'] += ';' + local_bpy_package_path.as_posix()
        if sys.platform == "win32":
            activate_script = self.venv_path / 'Scripts' / 'activate.bat'
            command = f'start cmd.exe /K && "{activate_script}"'
        else:
            raise NotImplementedError
            # activate_script = self.venv_path / 'bin' / 'activate'
            # command = f'source {activate_script}'
        subprocess.Popen(command, shell=True, env=os.environ)


class BlenderVenvManager:
    """
    A static class for collecting managing Blender virtual environments related functions. This class should not be
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


if __name__ == '__main__':
    blender_venv_path = Path(r'c:\TechDepot\Github\bermesio\_data\venvs\venv_blender_4.0.1_1')
    if blender_venv_path.exists():
        venv = BlenderVenv(blender_venv_path, store_in_pool=True)
        venv.launch_shell()
