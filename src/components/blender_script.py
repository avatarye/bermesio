import os
from pathlib import Path
import shutil

from commons.common import Result, blog, Dillable, SharedFunctions as SF
from config import Config


class BlenderScript(Dillable):
    """
    A base class representing a Blender script, which is always a single arbitrary Python script.
    """

    name = 'unknown_script'

    regular_script_deploy_subdir = f'{Config.app_name.lower()}_scripts'  # must be the same as BlenderSetup class's
    startup_script_deploy_subdir = 'startup'

    def __init__(self, script_path, repo_dir=None, delete_existing=False):
        """
        Initialize a BlenderScript object with a script path. If the script path is valid, the script will be copied to
        the repo_dir if it is given.

        :param script_path: a Path object of the script path
        :param repo_dir: a Path object of the repo directory to store the script
        :param delete_existing: a flag indicating whether to delete the existing script at the repo_dir
        """
        super().__init__()
        self.script_path = Path(script_path)
        if script_path.exists() and script_path.is_file() and script_path.suffix == '.py':
            self.name = self.script_path.stem
            if repo_dir:
                self._store_in_repo(repo_dir, delete_existing=delete_existing)
        else:
            raise FileNotFoundError(f'Valid Blender script not found at {self.script_path}')

    def _store_in_repo(self, repo_dir, delete_existing=False) -> Result:
        """
        Store this script in the repo_dir. If the script already exists in the repo_dir, it will be overwritten if the
        delete_existing flag is set to True.

        :param repo_dir: a Path object of the repo directory to store the script
        :param delete_existing: a flag indicating whether to delete the existing script at the repo_dir

        :return: a Result object indicating whether the storage is successful
        """
        repo_script_path = Path(repo_dir) / self.script_path.name
        result = SF.ready_target_path(repo_script_path, ensure_parent_dir=True, delete_existing=delete_existing)
        if not result:
            return result
        if not repo_script_path.exists():
            try:
                shutil.copy(self.script_path, repo_script_path)
            except OSError:
                return Result(False, f'Error copying script to {repo_script_path}.')
            if repo_script_path.exists():
                self.script_path = repo_script_path
                return Result(True)
        else:
            return Result(False, f'Error copying script to {repo_script_path}')

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
                deployed_target_path = deploy_dir / self.regular_script_deploy_subdir / self.script_path.name
            elif isinstance(self, BlenderDevStartupScript) or isinstance(self, BlenderStartupScript):
                deployed_target_path = deploy_dir / self.startup_script_deploy_subdir / self.script_path.name
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
                    os.symlink(self.script_path, deployed_target_path)
                except OSError:
                    return Result(False, f'Error creating symlink to script at {deployed_target_path}. If you are using'
                                         f' Windows, please try again with administrator privilege.')
                if deployed_target_path.exists():
                    blog(2, f'Symlinked development script {self.name} to {deployed_target_path} successfully')
                    return Result(True)
                else:
                    return Result(False, f'Error symlinking development script to {deployed_target_path}')
            elif isinstance(self, BlenderRegularScript) or isinstance(self, BlenderStartupScript):
                # Copy the script to the deploy_dir's subdirectory
                try:
                    shutil.copy(self.script_path, deployed_target_path)
                except OSError:
                    return Result(False, f'Error copying script to {deployed_target_path}.')
                if deployed_target_path.exists():
                    blog(2, f'Deployed script {self.name} to {deployed_target_path} successfully')
                    return Result(True)
                else:
                    return Result(False, f'Error deploying script to {deployed_target_path}')
            else:
                raise NotImplementedError(f'Script type {self.__class__} is not supported')
        else:
            return Result(False, f'Error deploying script to {deploy_dir}. Script not found at {self.script_path}')

    def verify(self) -> bool:
        """
        Verify if the script is valid. This is often called after restored from a dilled object.

        :return: a flag indicating whether the script is valid
        """
        return self.script_path.exists()

    def compare_name(self, other) -> bool:
        """
        Compare the name of this script with another script. This is often called for the purpose of updating the
        script in the repository.

        :param other: another BlenderScript object

        :return: a flag indicating whether the name of this script is the same as the other script
        """
        if issubclass(other.__class__, BlenderScript):
            return self.name == other.name
        return False

    def __str__(self):
        return f'{self.__class__.__name__}: {self.name}'

    def __eq__(self, other: 'BlenderScript'):
        """
        The equality of 2 BlenderScript objects is determined by the addon path instead of the instance itself. If the
        instance equality is required, use compare_uuid() from Dillable class.

        :param other: another BlenderScript object

        :return: True if the Blender script path of this instance is the same as the other instance, otherwise False
        """
        if issubclass(other.__class__, BlenderScript):
            return self.script_path == other.script_path
        return False

    def __hash__(self):
        return hash(self.script_path.as_posix())


class BlenderRegularScript(BlenderScript):
    """
    A class representing a regular Blender script, which is a single arbitrary Python script that is copied to the
    repository and deployed to the Blender scripts' additional script subdirectory.
    """
    def __init__(self, script_path, repo_dir=None, delete_existing=False):
        super().__init__(script_path, repo_dir=repo_dir, delete_existing=delete_existing)


class BlenderStartupScript(BlenderScript):
    """
    A class representing a startup Blender script, which is a single arbitrary Python script that is copied to the
    repository and deployed to the Blender scripts' startup script subdirectory. Startup scripts are executed when
    Blender starts. It usually contains code to register Blender operators.
    """
    def __init__(self, script_path, repo_dir=None, delete_existing=False):
        super().__init__(script_path, repo_dir=repo_dir, delete_existing=delete_existing)


class BlenderDevRegularScript(BlenderScript):
    """
    A class representing a development regular Blender script, which is a single arbitrary Python script that is
    symlinked to the Blender scripts' additional script subdirectory.
    """
    def __init__(self, script_path):
        super().__init__(script_path, repo_dir=None, delete_existing=False)

    def _store_in_repo(self, repo_dir, delete_existing=False) -> Result:
        raise NotImplementedError


class BlenderDevStartupScript(BlenderScript):
    """
    A class representing a development startup Blender script, which is a single arbitrary Python script that is
    symlinked to the Blender scripts' startup script subdirectory. Startup scripts are executed when Blender starts.
    It usually contains code to register Blender operators.
    """
    def __init__(self, script_path):
        super().__init__(script_path, repo_dir=None, delete_existing=False)

    def _store_in_repo(self, repo_dir, delete_existing=False) -> Result:
        raise NotImplementedError


class BlenderScriptManager:
    """
    A statis class for creating BlenderScript objects and other related functions falls outside the scope of the
    BlenderScript class.
    """

    def __new__(cls, *args, **kwargs):
        raise Exception('This class should not be instantiated.')

    @staticmethod
    def create_blender_script(script_path: str or Path, script_type: str, repo_dir=None, delete_existing=False) \
            -> Result:
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
        try:
            script_instance = script_class(script_path, repo_dir=repo_dir, delete_existing=delete_existing)
            if script_instance.verify():
                blog(2, 'Blender script instance created successfully')
                return Result(True, 'Blender script instance created successfully', script_instance)
        except Exception as e:
            return Result(False, f'Error creating Blender script instance: {e}', e)

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
        try:
            script_instance = script_class(script_path)
            if script_instance.verify():
                blog(2, 'Blender development script instance created successfully')
                return Result(True, 'Blender development script instance created successfully', script_instance)
        except Exception as e:
            return Result(False, f'Error creating Blender development script instance: {e}', e)
