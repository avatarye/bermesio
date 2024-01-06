from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess

from commons.common import Result, Dillable, blog, SharedFunctions as SF
from components.blender_addon import BlenderAddon
from components.blender_program import BlenderProgram
from components.blender_script import BlenderScript
from components.blender_setup import BlenderSetup
from components.blender_venv import BlenderVenv
from config import Config


@dataclass
class LaunchConfig:
    launch_type: str = 'blender'  # 'blender' or 'python'
    if_use_custom_setup: bool = True
    if_include_venv_python_packages: bool = True
    if_include_venv_bpy_package: bool = True
    if_include_venv_dev_libraries: bool = True
    if_include_addons: bool = True
    if_include_dev_addons: bool = True
    included_addon_list: [BlenderAddon] = None
    if_include_startup_scripts: bool = True
    if_include_regular_scripts: bool = True
    included_script_list: [BlenderScript] = None


class Profile(Dillable):

    def __init__(self, name, repo_profile_dir, init_dict=None):
        super().__init__()
        self.name = self._get_validated_profile_name(name)
        self.profile_dir = self._get_validated_profile_dir(repo_profile_dir)
        self.blender_program: BlenderProgram = init_dict.get('blender_program', None)
        self.blender_venv: BlenderVenv = init_dict.get('blender_venv', None)
        self.blender_addons: [BlenderAddon] = init_dict.get('blender_addons', [])
        self.blender_scripts: [BlenderScript] = init_dict.get('blender_scripts', [])

        self.custom_config_dir = None
        self.custom_script_dir = None
        self.custom_addon_dir = None
        self.custom_startup_script_dir = None
        self.custom_additional_script_dir = None

    def _get_validated_profile_name(self, name) -> str:
        if SF.is_valid_name_for_path(name):
            return name
        else:
            raise ValueError(f'Invalid profile name {name}')

    def _get_validated_profile_dir(self, repo_profile_dir: str or Path) -> Path:
        """
        Validate the profile directory inside the repo profile dir. If it not exists, create it.

        :param repo_profile_dir: a str or Path object of the path to the repo profile directory

        :return: a Path object of the validated profile directory
        """
        repo_profile_dir = Path(repo_profile_dir)
        result = SF.create_target_dir(repo_profile_dir)
        if not result:
            raise Exception(f'Error validating profile directory in the repository at {repo_profile_dir}')
        profile_dir = repo_profile_dir / f'.{self.name}'
        result = SF.create_target_dir(profile_dir)
        if not result:
            raise Exception(f'Error validating the profile directory at {profile_dir}')
        return profile_dir

    def set_blender_program(self, blender_program: BlenderProgram):
        self.blender_program = blender_program

    def set_blender_venv(self, blender_venv: BlenderVenv):
        if blender_venv.blender_program == self.blender_program:
            self.blender_venv = blender_venv
        else:
            self.blender_venv = None
            blog(3, f'Blender venv {blender_venv} does not match the Blender program {self.blender_program}')

    def add_blender_addons(self, blender_addons: [BlenderAddon]):
        self.blender_addons.extend(blender_addons)

    def add_blender_scripts(self, blender_scripts: [BlenderScript]):
        self.blender_scripts.extend(blender_scripts)

    def _create_custom_config_dir(self):
        custom_config_dir = self.profile_dir / 'config'
        if not custom_config_dir.exists():
            os.makedirs(custom_config_dir)
        if custom_config_dir.exists() and custom_config_dir.is_dir():
            self.custom_config_dir = custom_config_dir
        else:
            raise Exception(f'Error creating custom config directory at {custom_config_dir}')

    def _create_custom_script_dir(self):

        def create_sub_dir(sub_dir_name):
            sub_dir = custom_script_dir / sub_dir_name
            if not sub_dir.exists():
                os.makedirs(sub_dir)
            if sub_dir.exists() and sub_dir.is_dir():
                return sub_dir
            else:
                raise Exception(f'Error creating sub-directory in custom script directory at {sub_dir}')

        # create a custom script directory with an addons and startup subdirectory
        custom_script_dir = self.profile_dir / 'scripts'
        if not custom_script_dir.exists():
            os.makedirs(custom_script_dir)
        if custom_script_dir.exists() and custom_script_dir.is_dir():
            self.custom_script_dir = custom_script_dir
            self.custom_addon_dir = create_sub_dir('addons')
            self.custom_startup_script_dir = create_sub_dir('startup')
            self.custom_additional_script_dir = create_sub_dir(f'{Config.app_name.lower()}_scripts')
        else:
            raise Exception(f'Error creating custom script directory at {custom_script_dir}')

    def _deploy_addons_in_custom_script_dir(self):
        if self.custom_script_dir is not None:
            err_messages = []
            for blender_addon in self.blender_addons:
                try:
                    blender_addon.deploy(self.custom_addon_dir, delete_existing=True)
                except Exception as e:
                    err_messages.append(f'Error deploying addon {blender_addon.name}: {e}')

    def _deploy_scripts_in_custom_script_dir(self):
        pass

    def configure_venv(self):
        pass

    def launch_venv_in_shell(self, add_local_libs=True, add_bpy_path=True):
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

    # os.environ['BLENDER_USER_SCRIPTS'] = r'c:\TechDepot\AvatarTools\Blender\Launcher\shared_scripts'
    # os.environ['BLENDER_USER_CONFIG'] = r'c:\Users\yong-\.source\config'

    def launch_blender(blender_path, env_path):
        if sys.platform == "win32":
            activate_script = env_path / 'Scripts' / 'activate.bat'
            command = f'cmd.exe /c "{activate_script} && "{blender_path}"'
        else:
            activate_script = env_path / 'bin' / 'activate'
            command = f'source {activate_script} && "{blender_path}"'
        return run_command(command)

    def verify(self) -> bool:
        return True

    def __str__(self):
        return f'Profile: {self.name}'

    def __eq__(self, other: 'Profile'):
        """
        The equality of 2 Profile objects is determined by the addon path instead of the instance itself. If the
        instance equality is required, use compare_uuid() from Dillable class.

        :param other: another Profile object

        :return: True if the Profile path of this instance is the same as the other instance, otherwise False
        """
        if issubclass(other.__class__, Profile):
            return self.profile_dir == other.profile_dir
        return False

    def __hash__(self):
        return hash(self.profile_dir.as_posix())


class ProfileManager:

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def create_profile(cls, name, repo_profile_dir, init_dict=None) -> Profile:
        return Profile(name, repo_profile_dir, init_dict=init_dict)

r'mklink "c:\TechDepot\AvatarTools\Blender\Launcher\stable\blender-3.6.7-windows-x64\3.6\scripts\addons\bermesio_cone_creator.py" "c:\TechDepot\Github\bermesio\_data\test_data\dev\bermesio_cone_creator.py'