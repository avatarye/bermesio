from dataclasses import dataclass
import os
import sys
import subprocess

from commons.common import Result, ResultList, blog, SharedFunctions as SF
from commons.command import run_command, popen_command
from components.blender_program import BlenderProgram
from components.blender_setup import BlenderSetup
from components.blender_venv import BlenderVenv
from components.component import Component
from config import Config


@dataclass
class BlenderLaunchConfig:
    if_use_blender_setup_config: bool = True
    if_use_blender_setup_addons_scripts: bool = True
    if_include_venv_site_packages: bool = True
    if_include_venv_bpy: bool = False
    if_include_venv_local_libs: bool = True


@dataclass
class VenvLaunchConfig:
    if_include_venv_bpy: bool = True
    if_include_venv_local_libs: bool = True


class Profile(Component):

    def __init__(self, name):
        super().__init__(None)
        self.dill_extension = Config.get_dill_extension(self)
        self.__class__.dill_extension = self.dill_extension
        self.is_renamable = True
        self.is_duplicable = True
        self.init_params = {'name': name}

    def create_instance(self) -> Result:
        self.name = self.init_params['name']
        if SF.is_valid_name_for_path(self.name):
            self.blender_program: BlenderProgram = None
            self.blender_setup: BlenderSetup = None
            self.blender_venv: BlenderVenv = None
            return Result(True, f'Profile {self.name} created', self)
        else:
            return Result(False, f'Invalid name for Profile: {self.name}')

    def add_component(self, component: Component) -> Result:
        if isinstance(component, BlenderProgram):
            if component.verify():
                self.blender_program = component
                return Result(True, f'BlenderProgram {component.name} added to Profile {self.name}')
            else:
                return Result(False, f'BlenderProgram {component.name} cannot be added to Profile {self.name}')
        elif isinstance(component, BlenderSetup):
            if component.verify():
                self.blender_setup = component
                return Result(True, f'BlenderSetup {component.name} added to Profile {self.name}')
            else:
                return Result(False, f'BlenderSetup {component.name} cannot be added to Profile {self.name}')
        elif isinstance(component, BlenderVenv):
            if component.verify():
                # Verify if the BlenderVenv was created from the same BlenderProgram as the one in this Profile
                if self.blender_program is None:
                    return Result(False, f'BlenderVenv cannot be set before BlenderProgram for Profile {self.name}')
                else:
                    if component.blender_program == self.blender_program:
                        self.blender_venv = component
                        return Result(True, f'BlenderVenv {component.name} added to Profile {self.name}')
                    else:
                        return Result(False, f'BlenderVenv {component.name} was created from a different '
                                             f'BlenderProgram than the one in Profile {self.name}')
            else:
                return Result(False, f'BlenderVenv {component.name} cannot be added to Profile {self.name}')
        else:
            return Result(False, f'Component type {component.__class__.__name__} cannot be added to Profile '
                                 f'{self.name}')

    def launch_blender(self, launch_config: BlenderLaunchConfig = BlenderLaunchConfig()) -> Result:
        if self.blender_program is not None:
            # Set BlenderSetup's config and scripts as environment variables for Blender to use
            if self.blender_setup is not None and launch_config.if_use_blender_setup_config:
                user_config_path = self.blender_setup.data_path / self.blender_setup.setup_blender_config_path
                os.environ['BLENDER_USER_CONFIG'] = str(user_config_path)
            if self.blender_setup is not None and launch_config.if_use_blender_setup_addons_scripts:
                user_script_path = self.blender_setup.data_path / self.blender_setup.setup_scripts_path
                os.environ['BLENDER_USER_SCRIPTS'] = str(user_script_path)

            # Set pth file to include venv's site-packages, bpy, and local libraries for Blender to use
            if self.blender_venv is not None:
                # Always remove the pth file first
                result = self.blender_venv.remove_blender_pth()
                if not result:
                    return result
                if launch_config.if_include_venv_site_packages:
                    result = self.blender_venv.add_site_packages_to_blender_pth()
                    if not result:
                        return result
                if launch_config.if_include_venv_bpy:
                    result = self.blender_venv.add_bpy_package_to_blender_pth()
                    if not result:
                        return result
                if launch_config.if_include_venv_local_libs:
                    result = self.blender_venv.add_dev_libraries_to_blender_pth()
                    if not result:
                        return result

            # Launch Blender
            blender_exe_path = self.blender_program.data_path / self.blender_program.blender_exe_path
            if blender_exe_path.exists():
                if sys.platform == "win32":
                    command = f'cmd.exe /k start cmd.exe /c "{blender_exe_path}"'
                else:
                    raise NotImplementedError
                    # command = f'source {activate_script} && "{blender_exe_path}"'
                popen_command(command, os_env=os.environ)
                return Result(True, f'Blender launched successfully')
            else:
                return Result(False, f'Blender executable not found at {blender_exe_path}')
        else:
            return Result(False, f'BlenderProgram is not set for Profile {self.name}')

    def configure_venv(self, launch_config: VenvLaunchConfig = VenvLaunchConfig()) -> Result:
        if self.blender_program is not None:
            if self.blender_venv is not None:
                # Always remove the pth file first
                result = self.blender_venv.remove_venv_pth()
                if not result:
                    return result
                if launch_config.if_include_venv_bpy:
                    result = self.blender_venv.add_bpy_package_to_venv_pth()
                    if not result:
                        return result
                if launch_config.if_include_venv_local_libs:
                    result = self.blender_venv.add_dev_libraries_to_venv_pth()
                    if not result:
                        return result
                return Result(True, f'Venv configured successfully', self.blender_venv.data_path)
            else:
                return Result(False, f'Blender venv is not set for Profile {self.name}')
        else:
            return Result(False, f'Blender program is not set for Profile {self.name}')

    def launch_venv(self, launch_config: VenvLaunchConfig = VenvLaunchConfig()) -> Result:
        result = self.configure_venv(launch_config)
        if not result:
            return result
        # Launch venv
        activate_script = self.blender_venv.get_activate_script_path()
        if activate_script is not None:
            if sys.platform == "win32":
                command = f'cmd.exe /k start cmd.exe /k "{activate_script}"'
            else:
                # command = f'source {activate_script}'
                raise NotImplementedError
            popen_command(command)
            return Result(True, f'Blender venv launched successfully')
        else:
            return Result(False, f'Blender venv activate script not found')

    def verify(self) -> bool:
        return all([
            True if self.blender_program is None else self.blender_program.verify(),
            True if self.blender_setup is None else self.blender_setup.verify(),
            True if self.blender_venv is None else self.blender_venv.verify(),
        ])

    def __str__(self):
        return f'{self.__class__.__name__}: {self.name}'

    def __eq__(self, other: 'Profile'):
        """
        The equality of 2 Profile objects is determined by its name.

        :param other: another Profile object

        :return: True if equal, otherwise False
        """
        if issubclass(other.__class__, Profile):
            return self.name == other.name
        return False

    def __hash__(self):
        return self.get_stable_hash(self.name)


class ProfileManager:

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def create(cls, name: str) -> Result:
        return Profile(name).create_instance()
