import hashlib
import os
from pathlib import Path
import shutil

from commons.common import Result, blog, SharedFunctions as SF
from components.component import Component
from config import Config


class BlenderScript(Component):
    """
    A base class representing a Blender script, which is always a single arbitrary Python script.
    """

    name = 'unknown_script'

    regular_script_deploy_subdir = f'{Config.app_name.lower()}_scripts'  # must be the same as BlenderSetup class's
    startup_script_deploy_subdir = 'startup'

    def __init__(self, script_path: str or Path):
        """
        Initialize a BlenderScript object with a script path.

        :param script_path: a str or Path object of the script path
        """
        super().__init__(script_path)
        self.dill_extension = Config.get_dill_extension(self)
        self.__class__.dill_extension = self.dill_extension
        self.if_store_in_repo = True
        self.is_renamable = False
        self.is_upgradeable = False
        self.is_duplicable = False
        self.init_params = {'script_path': script_path}

    def create_instance(self) -> Result:
        """
        Create a BlenderScript object based on the script path.

        :return: a Result object indicating if the initialization is successful and the message generated during the
                 initialization, and this object if successful.
        """
        if self.data_path is not None:
            if self.data_path.is_file() and self.data_path.suffix == '.py':
                self.name = self.data_path.stem
                return Result(True, f'Blender script instance created successfully.', self)
        else:
            return Result(False, f'Blender script file is not valid ath not found at {self.data_path}')

    def deploy(self, deploy_dir: str or Path, delete_existing=False) -> Result:
        """
        Deploy this script to the deploy_dir's subdirectory depending on its type. If this is a development script, a
        symlink will be created at the deploy_dir. Regular scripts will be copied to the deploy_dir/bermesio_scripts,
        startup scripts will be copied to the deploy_dir/startup

        :param deploy_dir: the directory to deploy this script to, typically the scripts directory of a Blender setup
        :param delete_existing: a flag indicating whether to delete the existing script at the deploy_dir

        :return: a Result object indicating whether the deployment is successful
        """
        deploy_dir = Path(deploy_dir)
        if self.verify():
            # Ready the target directory or file path for deployment
            if isinstance(self, BlenderDevRegularScript) or isinstance(self, BlenderRegularScript):
                deployed_target_path = deploy_dir / self.regular_script_deploy_subdir / self.data_path.name
            elif isinstance(self, BlenderDevStartupScript) or isinstance(self, BlenderStartupScript):
                deployed_target_path = deploy_dir / self.startup_script_deploy_subdir / self.data_path.name
            else:
                raise NotImplementedError(f'Script type {self.__class__} is not supported')
            result = SF.ready_target_path(deployed_target_path, ensure_parent_dir=True, delete_existing=delete_existing)
            if not result:
                return result
            # All non-development scripts will be copied to the target deploy path, while development scripts will be
            # symlinked.
            if isinstance(self, BlenderDevRegularScript) or isinstance(self, BlenderDevStartupScript):
                # Create a symlink to the script at the deploy_dir's subdirectory
                try:
                    os.symlink(self.data_path, deployed_target_path)
                except OSError:
                    return Result(False, f'Error creating symlink to script at {deployed_target_path}. If you are using'
                                         f' Windows, please try again with administrator privilege.')
                if deployed_target_path.exists():
                    blog(2, f'Symlinked development script {self.name} to {deployed_target_path} successfully')
                    return Result(True, '', deployed_target_path)
                else:
                    return Result(False, f'Error symlinking development script to {deployed_target_path}')
            elif isinstance(self, BlenderRegularScript) or isinstance(self, BlenderStartupScript):
                # Copy the script to the deploy_dir's subdirectory
                try:
                    shutil.copy(self.data_path, deployed_target_path)
                except OSError:
                    return Result(False, f'Error copying script to {deployed_target_path}.')
                if deployed_target_path.exists():
                    blog(2, f'Deployed script {self.name} to {deployed_target_path} successfully')
                    return Result(True, '', deployed_target_path)
                else:
                    return Result(False, f'Error deploying script to {deployed_target_path}')
            else:
                raise NotImplementedError(f'Script type {self.__class__} is not supported')
        else:
            return Result(False, f'Error deploying script to {deploy_dir}. Script not found at {self.data_path}')

    def __str__(self):
        return f'{self.__class__.__name__}: {self.name}'

    def __eq__(self, other):
        """
        The equality of 2 BlenderScript instances is determined its name.

        :param other: another BlenderScript object

        :return: True if equal, otherwise False
        """
        if issubclass(other.__class__, BlenderScript):
            return self.name == other.name

    def __hash__(self):
        """
        The hash of a BlenderScript object is the hash value of its name.

        :return: a hash value of the data path
        """
        return self.get_stable_hash(self.name)


class BlenderReleasedScript(BlenderScript):
    """
    This is an intermediary class simply serves as a grouping purpose. It is inherited by BlenderRegularScript and
    BlenderStartupScript.
    """
    ...


class BlenderRegularScript(BlenderReleasedScript):
    """
    A class representing a regular Blender script, which is a single arbitrary Python script that is copied to the
    repository and deployed to the Blender scripts' additional script subdirectory.
    """
    def __init__(self, script_path):
        super().__init__(script_path)


class BlenderStartupScript(BlenderReleasedScript):
    """
    A class representing a startup Blender script, which is a single arbitrary Python script that is copied to the
    repository and deployed to the Blender scripts' startup script subdirectory. Startup scripts are executed when
    Blender starts. It usually contains code to register Blender operators.
    """
    def __init__(self, script_path):
        super().__init__(script_path)


class BlenderDevScript(BlenderScript):
    """
    This is an intermediary class simply serves as a grouping purpose. It is inherited by BlenderDevRegularScript and
    BlenderDevStartupScript.
    """
    def __init__(self, script_path: str or Path):
        self.if_store_in_repo = False
        super().__init__(script_path)

    def _store_in_repo(self, repo_dir, delete_existing=False) -> Result:
        raise NotImplementedError


class BlenderDevRegularScript(BlenderDevScript):
    """
    A class representing a development regular Blender script, which is a single arbitrary Python script that is
    symlinked to the Blender scripts' additional script subdirectory.
    """
    def __init__(self, script_path):
        super().__init__(script_path)


class BlenderDevStartupScript(BlenderDevScript):
    """
    A class representing a development startup Blender script, which is a single arbitrary Python script that is
    symlinked to the Blender scripts' startup script subdirectory. Startup scripts are executed when Blender starts.
    It usually contains code to register Blender operators.
    """
    def __init__(self, script_path):
        super().__init__(script_path)


class BlenderScriptManager:
    """
    A statis class for creating BlenderScript objects and other related functions falls outside the scope of the
    BlenderScript class.
    """

    def __new__(cls, *args, **kwargs):
        raise Exception('This class should not be instantiated.')

    @staticmethod
    def create_blender_script(script_path: str or Path, script_type: str) -> Result:
        """
        Create a BlenderScript object based on the specified type. It will return a Result object indicating whether
        the creation is successful with the BlenderScript object as the data if successful.

        :param script_path: a str or Path object of the script path
        :param script_type: the type of the script, which is a string of either 'regular' or 'startup'
        :param repo_dir: a Path object of the repo directory to store the script
        :param delete_existing: a flag indicating whether to delete the existing script at the repo_dir

        :return: a Result object indicating whether the creation is successful with the BlenderScript object as the
                 data if successful
        """
        script_path = Path(script_path)
        if script_type == 'regular':
            script_class = BlenderRegularScript
        elif script_type == 'startup':
            script_class = BlenderStartupScript
        else:
            return Result(False, f'Invalid script type {script_type}')
        blog(2, 'Creating a Blender script instance...')
        return script_class(script_path).create_instance()

    @staticmethod
    def create_blender_dev_script(script_path: str or Path, script_type: str) -> Result:
        """
        Create a development BlenderScript object based on the specified type. It will return a Result object indicating
        whether the creation is successful with the BlenderScript object as the data if successful.

        :param script_path: a str or Path object of the script path
        :param script_type: the type of the script, which is a string of either 'regular' or 'startup'

        :return: a Result object indicating whether the creation is successful with the BlenderScript object as the
                 data if successful
        """
        script_path = Path(script_path)
        if script_type == 'regular':
            script_class = BlenderDevRegularScript
        elif script_type == 'startup':
            script_class = BlenderDevStartupScript
        else:
            return Result(False, f'Invalid development script type {script_type}')
        blog(2, 'Creating a Blender development script instance...')
        return script_class(script_path).create_instance()
