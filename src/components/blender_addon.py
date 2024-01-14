import ast
import os
from pathlib import Path
import re
import shutil
import zipfile

from packaging.version import Version

from commons.common import Result, blog, SharedFunctions as SF
from components.component import Component
from config import Config


class BlenderAddon(Component):
    """
    A class representing a Blender addon with necessary information, including the addon name, version, Blender version,
    and description. It supports the Blender addons packed in the following ways:
    1. A zipped single-file addon, containing only one non-init Python file with bl_info at arbitrary level.
    2. A zipped regular addon, containing a __init__.py file with bl_info at top level or one level down.
    3. A directory based regular addon containing a __init__.py file with bl_info at top level.
    4. A single-file addon based a single non-init Python file with bl_info.
    Note: Single-file addon refers to an addon that has only one Python file, which must not be __init__.py.
    Technically, a regular addon can have only one __init__.py file, but it is not considered as a single-file addon,
    for Blender requires it to be placed in a directory within Blender's addon directory, while single-file addon must
    be placed directly in the addon directory.

    Above formats will be handled by these 3 subclasses respectively, BlenderZippedAddon, BlenderDirectoryAddon, and
    BlenderSingleFileAddon. Each subclass will pack the addon to the addon repository using a unified zipped format as
    follows:
    - Non-single file addon:
      addon_sub_repo_path/[addon_name]_[addon_version].zip
                            |
                            <addon_name>
                              |
                              __init__.py
    - Single file addon:
      addon_sub_repo_path/[addon_name]_[addon_version].zip
                            |
                            [addon_name].py
    Above zipped formats can be unpacked directly into the target Blender addon directory.

    Non-zipped formats can also be used as development addon types, which will be handled by these 2 subclasses,
    BlenderDevDirectoryAddon and BlenderDevSingleFileAddon. They will not be stored in the addon repo and only be
    symlinked to the target Blender addon to make the code editable.
    """

    # region Initialization

    name, version, blender_version_min, description = None, None, None, None

    # A name used in the repository GUI, i.e., "Fluent 1.0.0"
    repo_name = 'Unknown Addon'
    # A name for the addon zip file stored in the repository, i.e., "fluent_1.0.0.zip"
    repo_zip_file_name = 'unknown_addon.zip'
    # A name for the dev addon directory when deployed in Blender Addons path as a directory symlink
    symlinked_dir_name = 'unknown_addon'
    # A name for the dev addon single file when deployed in Blender Addons path as a file symlink
    symlinked_single_file_name = 'unknown_addon.py'

    def __init__(self, addon_path: str or Path):
        """
        Create a BlenderAddon object from the addon path. This is usually not directly called. The recommended way is to
        use BlenderAddonManager.create_blender_addon() to create a BlenderAddon object, which will automatically detect
        the addon type and use the corresponding subclass, and then call creat_instance method.

        :param addon_path: A path to the addon, which can be a zip file, a directory, or a single Python file.
        :param repo_dir: A path to the addon repository, which is used to store the addon in the repository.
        :param delete_existing: A flag indicating if the existing addon in the repository should be deleted.
        """
        super().__init__(addon_path)
        self.dill_extension = Config.get_dill_extension(self)
        self.__class__.dill_extension = self.dill_extension
        self.if_store_in_repo = True
        self.is_renamable = False
        self.is_upgradeable = True
        self.is_duplicable = False
        self.init_params = {'addon_path': addon_path}

    def _get_addon_init_file_content(self) -> str or None:
        """This method should be implemented in subclasses."""
        raise NotImplementedError

    def _get_addon_info(self) -> (str or None, Version or None, Version or None, str or None):
        """
        Get the addon name, version, Blender version, and description from the bl_info dictionary in the addon.

        :return: a tuple of addon name, version, Blender version, and description
        """
        init_file_content = self._get_addon_init_file_content()
        if init_file_content is not None:
            match = re.search(r'bl_info\s*=\s*{.*?}', init_file_content, re.DOTALL)
            if match:
                bl_info_block = match.group(0)
                match = re.search(r'bl_info\s*=\s*({.*?})', bl_info_block, re.DOTALL)
                if match:
                    dict_string = match.group(1)
                    try:
                        bl_info_dict = ast.literal_eval(dict_string)
                        return (bl_info_dict.get('name', None),
                                Version('.'.join([str(i) for i in bl_info_dict.get('version')]))
                                if bl_info_dict.get('version') else None,
                                Version('.'.join([str(i) for i in bl_info_dict.get('blender')]))
                                if bl_info_dict.get('blender') else None,
                                bl_info_dict.get('description', None))
                    except SyntaxError:
                        pass
        return None, None, None, None

    def create_instance(self) -> Result:
        """
        Create a BlenderAddon object based on an existing Blender addon path. This method will detect the addon type
        and use the corresponding subclass to create the instance.

        :return: a Result object indicating if the initialization is successful, the message generated during the
                 initialization, and this object if successful.
        """
        if self.data_path is not None:
            self.name, self.version, self.blender_version_min, self.description = self._get_addon_info()
            # At least name and version must be available to be a valid Blender addon
            if None not in [self.name, self.version]:
                self.repo_name = f'{self.name} {self.version}'
                self.repo_zip_file_name = f'{self.repo_name.replace(" ", "_").lower()}.zip'
                # Use detected addon name to allow the input path named freely, such as "src" or "addon"
                self.symlinked_dir_name = self.name.replace(" ", "_").lower()
                # Use the original name for the single file addon to avoid confusion
                self.symlinked_single_file_name = self.data_path.name
                return Result(True, f'Created Blender addon from {self.data_path}', self)
            else:
                return Result(False, f'Error getting Blender addon information in {self.data_path}')
        else:
            return Result(False, f'Error creating Blender addon: {self.data_path} does not exist')

    # endregion

    def deploy(self, deploy_dir: str or Path, delete_existing: bool =False) -> Result:
        """
        Deploy this addon to target Blender addon directory. In case of non-development subclass, this method will
        unzip the addon zip to the target directory. Otherwise, it will create a symlink to the addon at the target
        directory. Based on the addon type, the addon will be deployed in different ways:
        - Single-file addon will be deployed as a single file or a symlink to the single file in the addon directory.
        - Regular addon will be deployed as a directory or a symlink to the original directory in the addon directory.

        :param deploy_dir: target Blender addon director
        :param delete_existing: a flag indicating if the existing addon in the target directory should be deleted
        :return: a Result object indicating if the deployment is successful
        """
        deploy_dir = Path(deploy_dir)
        if self.verify():
            # Ready the target directory or file path for deployment
            if isinstance(self, BlenderDevDirectoryAddon):
                deployed_target_path = deploy_dir / self.symlinked_dir_name
                result = SF.ready_target_path(deployed_target_path, ensure_parent_dir=True,
                                              delete_existing=delete_existing)
            elif isinstance(self, BlenderDevSingleFileAddon):
                deployed_target_path = deploy_dir / self.symlinked_single_file_name
                result = SF.ready_target_path(deployed_target_path, ensure_parent_dir=True,
                                              delete_existing=delete_existing)
            else:
                deployed_target_path = deploy_dir
                # Get the unzipped directory name or file name and ready it for deployment
                unzipped_path = None
                with zipfile.ZipFile(self.data_path, 'r') as z:
                    if len(z.namelist()) == 1:  # Single file addon
                        unzipped_path = deployed_target_path / Path(z.namelist()[0]).name
                    else:  # Non-single file addon
                        for file in z.namelist():
                            if '/' in file:
                                unzipped_path = deployed_target_path / file.split('/')[0]
                                break
                if unzipped_path is None:
                    return Result(False, f'Error deploying addon to {deploy_dir}: addon zip appears to be invalid')
                result = SF.ready_target_path(unzipped_path, ensure_parent_dir=True, delete_existing=delete_existing)
            if not result:
                return result
            # All non-development addons will be deployed in the same way, which is to unzip the addon zip stored in the
            # repository to the target directory.
            if isinstance(self, BlenderDevDirectoryAddon) or isinstance(self, BlenderDevSingleFileAddon):
                # Create a symlink to the addon at the deploy_dir
                try:
                    os.symlink(self.data_path, deployed_target_path)
                except OSError:
                    return Result(False, f'Error creating symlink to addon at {deployed_target_path}. If you are using '
                                         f'Windows, please try again with administrator privilege.')
                if deployed_target_path.exists():
                    blog(2, f'Symlinked development addon {self.repo_name} to {deployed_target_path} successfully')
                    return Result(True, '', deployed_target_path)
                else:
                    return Result(False, f'Error symlinking addon to {deployed_target_path}')
            elif (isinstance(self, BlenderZippedAddon) or isinstance(self, BlenderDirectoryAddon)
                    or isinstance(self, BlenderSingleFileAddon)):
                # Unzip this addon into the custom_addon_dir
                with zipfile.ZipFile(self.data_path, 'r') as z:
                    if isinstance(self, BlenderSingleFileAddon):
                        extracted_name = z.namelist()[0]
                    else:
                        extracted_name = z.namelist()[0].split('/')[0]
                    z.extractall(deployed_target_path)
                # The path to the extracted addon directory or file
                extracted_path = deployed_target_path / extracted_name
                if extracted_path.exists():
                    blog(2, f'Deployed addon {self.repo_name} to {extracted_path} successfully')
                    return Result(True, '', extracted_path)
                else:
                    return Result(False, f'Error deploying addon to {deployed_target_path}')
            else:
                raise NotImplementedError(f'Addon type {self.__class__} is not supported')
        else:
            return Result(False, f'Error deploying addon to {deploy_dir}. Addon not found at {self.data_path}')

    def __str__(self):
        return f'{self.__class__.__name__}: {self.name} {self.version}'

    def __eq__(self, other: 'BlenderAddon'):
        """
        The equality of 2 BlenderAddon objects is determined by the addon name plus version.

        :param other: another BlenderAddon object

        :return: True if equal, otherwise False
        """
        if issubclass(other.__class__, BlenderAddon):
            return f'{self.name}|{self.version}' == f'{other.name}|{other.version}'
        return False

    def __hash__(self):
        return self.get_stable_hash(f'{self.name}|{self.version}')


class BlenderReleasedAddon(BlenderAddon):
    """
    This is an intermediary class simply serves as a grouping purpose. It is inherited by BlenderZippedAddon,
    BlenderDirectoryAddon, and BlenderSingleFileAddon.
    """
    ...


class BlenderZippedAddon(BlenderReleasedAddon):
    """
    A class representing a Blender addon in a zip file with necessary information, including the addon name, version,
    Blender version, and description. When storing the addon in the addon repository, it will intelligently rezip the
    files in a way that the resulting zip file can be unzipped directly into Blender's addon directory correctly and be
    recognized by Blender as a valid addon.
    """

    def __init__(self, addon_path: str or Path):
        """
        Create a BlenderZippedAddon object from the addon path.

        :param addon_path: a path to the addon, which must be a zip file
        """
        self.is_single_file_addon, self.if_rezip = False, False
        super().__init__(addon_path)

    def _get_addon_init_file_content(self) -> str or None:
        """
        Search for the addon entry file (__init__.py or single Python file) in the zipped addon and return its content.

        :return: string content of the addon entry file
        """

        def get_zipped_file_content(zip_filestream: zipfile.ZipFile, in_zip_file: str) -> str:
            """
            Get the content of a file in a zip file.

            :param zip_filestream: a ZipFile object
            :param in_zip_file: a file path in the zip file

            :return: string content of the file
            """

            with zip_filestream.open(in_zip_file, 'r') as zf:
                return zf.read().decode('utf-8')

        with zipfile.ZipFile(self.data_path, 'r') as z:
            zipped_files = [name for name in z.namelist() if not name.endswith('/') and not name.endswith('\\')]
            # Zipped single-file addon
            if len(zipped_files) == 1 and zipped_files[0].endswith('.py') \
                    and not zipped_files[0].endswith('__init__.py'):
                self.is_single_file_addon = True
                # If the single file addon is not at top level, flag it to be re-zipped.
                if '/' or '\\' in zipped_files[0]:
                    self.if_rezip = True
                return get_zipped_file_content(z, zipped_files[0])
            # Zipped regular addon
            else:
                self.is_single_file_addon = False
                # Search for __init__ at top level
                init_files = [name for name in z.namelist() if name.endswith('__init__.py')
                              and (name.count('/') + name[0].count('\\')) == 0]
                if len(init_files) == 1:
                    self.if_rezip = True
                    return get_zipped_file_content(z, init_files[0])
                # Search for __init__ one level down if not found at top level
                init_files = [name for name in z.namelist() if name.endswith('__init__.py')
                              and (name.count('/') + name[0].count('\\')) == 1]
                if len(init_files) == 1:
                    self.if_rezip = False
                    return get_zipped_file_content(z, init_files[0])
        return None

    def store_in_repo(self, repo_dir: str or Path, delete_existing: bool =False) -> Result:
        """
        Store the addon in the addon repository. Either copy or rezip the addon to the repository depending on the
        addon type and in-zip file structure.

        :param repo_dir: a path to the addon repository, which is used to store the addon in the repository
        :param delete_existing: a flag indicating if the existing addon in the repository should be deleted

        :return: a Result object indicating if the storage is successful
        """

        def rezip(input_zip_path, output_zip_path, top_dir_name):
            """
            Rezip the addon under 2 scenarios:
            1. Regular addon with __init__.py at top level
            2. Single-file addon with the Python file not at top level

            :param input_zip_path: a path to the original addon zip file
            :param output_zip_path: a path to the new addon zip file
            :param top_dir_name: a name for the top level directory in the new zip file
            """
            with zipfile.ZipFile(input_zip_path, 'r') as zr:
                with zipfile.ZipFile(output_zip_path, 'w') as zw:
                    if self.is_single_file_addon:
                        zipped_files = [name for name in zr.namelist() if
                                        not name.endswith('/') and not name.endswith('\\')]
                        new_path = Path(zipped_files[0]).name
                        zw.writestr(new_path, zr.read(zr.namelist()[0]))
                    else:
                        for item in zr.infolist():
                            data = zr.read(item.filename)
                            new_path = f"{top_dir_name}/{item.filename}"
                            zw.writestr(new_path, data)

        repo_addon_path = Path(repo_dir) / self.repo_zip_file_name
        result = SF.ready_target_path(repo_addon_path, ensure_parent_dir=True, delete_existing=delete_existing)
        if not result:
            return result
        if not repo_addon_path.exists():
            try:
                if self.if_rezip:
                    rezip(self.data_path, repo_addon_path, self.symlinked_dir_name)
                else:
                    shutil.copy(self.data_path, repo_addon_path)
            except OSError as e:
                return Result(False, f'Error copying addon to {repo_addon_path}: {e}')
            if repo_addon_path.exists():
                self.is_stored_in_repo = True
                self.repo_rel_path = repo_addon_path.relative_to(Config.repo_dir)
                self.data_path = repo_addon_path
                return Result(True)
            else:
                return Result(False, f'Error copying addon to {repo_addon_path}')
        else:
            return Result(False, f'Addon already exists in the repository at {repo_addon_path}')


class BlenderDirectoryAddon(BlenderReleasedAddon):
    """
    A class representing a Blender addon in a directory with necessary information, including the addon name, version,
    Blender version, and description. When storing the addon in the addon repository, it will pack the addon into a zip
    file. It only accepts a directory with a __init__.py file in it or a single Python file with bl_info in it.
    """

    def __init__(self, addon_path: str or Path):
        """
        Create a BlenderDirectoryAddon object from the addon path.

        :param addon_path: a path to the addon, which must be a directory
        """
        self.is_single_file_addon = False
        super().__init__(addon_path)

    def _get_addon_init_file_content(self) -> str or None:
        files = list(self.data_path.iterdir())
        # Search for the single-file Python addon file at top level
        if len(files) == 1 and files[0].name.endswith('.py') and files[0].name != '__init__.py':
            self.is_single_file_addon = True
            addon_entry_file_path = files[0]
        # Search for the __init__.py file at top level
        elif '__init__.py' in [f.name for f in files]:
            self.is_single_file_addon = False
            addon_entry_file_path = self.data_path / '__init__.py'
        else:
            return None
        with open(addon_entry_file_path, encoding='utf-8') as f:
            return f.read()

    def store_in_repo(self, repo_dir: str or Path, delete_existing: bool =False) -> Result:
        """
        Store the addon in the addon repository. Zip the addon to the repository depending on the addon type.

        :param repo_dir: a path to the addon repository, which is used to store the addon in the repository
        :param delete_existing: a flag indicating if the existing addon in the repository should be deleted

        :return: a Result object indicating if the storage is successful
        """
        repo_addon_path = Path(repo_dir) / self.repo_zip_file_name
        result = SF.ready_target_path(repo_addon_path, ensure_parent_dir=True, delete_existing=delete_existing)
        if not result:
            return result
        if not repo_addon_path.exists():
            try:
                # If a regular addon directory, zip it with the top level directory name.
                if not self.is_single_file_addon:
                    with zipfile.ZipFile(repo_addon_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for item in self.data_path.glob('**/*'):
                            if item.is_file():
                                zipf.write(item,
                                           arcname=f'{self.symlinked_dir_name}/{item.relative_to(self.data_path)}')
                # If a single-file addon directory, zip it directly.
                else:
                    files = [f.name for f in self.data_path.iterdir()]
                    with zipfile.ZipFile(repo_addon_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        zipf.write(self.data_path / files[0], arcname=files[0])
            except OSError as e:
                return Result(False, f'Error copying addon to {repo_addon_path}: {e}')
            if repo_addon_path.exists():
                self.is_stored_in_repo = True
                self.repo_rel_path = repo_addon_path.relative_to(Config.repo_dir)
                self.data_path = repo_addon_path
                return Result(True)
        else:
            Result(False, f'Error copying addon to {repo_addon_path}')


class BlenderSingleFileAddon(BlenderReleasedAddon):
    """
    A class representing a Blender addon with a single non-init Python file with necessary information, including the
    addon name, version, Blender version, and description.
    """

    def __init__(self, addon_path: str or Path):
        """
        Create a BlenderSingleFileAddon object from the addon path.

        :param addon_path: a path to the addon, which must be a single Python file
        """
        super().__init__(addon_path)

    def _get_addon_init_file_content(self) -> str or None:
        with open(self.data_path, encoding='utf-8') as f:
            return f.read()

    def store_in_repo(self, repo_dir: str or Path, delete_existing: bool =False) -> Result:
        repo_addon_path = Path(repo_dir) / self.repo_zip_file_name
        result = SF.ready_target_path(repo_addon_path, ensure_parent_dir=True, delete_existing=delete_existing)
        if not result:
            return result
        if not repo_addon_path.exists():
            try:
                with zipfile.ZipFile(repo_addon_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(self.data_path, arcname=self.data_path.name)
            except OSError as e:
                return Result(False, f'Error copying addon to {repo_addon_path}: {e}')
            if repo_addon_path.exists():
                self.is_stored_in_repo = True
                self.repo_rel_path = repo_addon_path.relative_to(Config.repo_dir)
                self.data_path = repo_addon_path
                return Result(True)
            else:
                return Result(False, f'Error copying addon to {repo_addon_path}')


class BlenderDevAddon(BlenderAddon):
    """
    This is an intermediary class simply serves as a grouping purpose. It is inherited BlenderDevDirectoryAddon, and
    BlenderDevSingleFileAddon.
    """

    def __init__(self, addon_path: str or Path):
        self.if_store_in_repo = False
        super().__init__(addon_path)

    def store_in_repo(self, repo_dir: str or Path, delete_existing: bool =False) -> Result:
        raise NotImplementedError('BlenderDevAddon cannot be stored in a repo')


class BlenderDevDirectoryAddon(BlenderDevAddon):
    """
    A class representing a Blender addon in development, which is a directory located in a non-repo path, typically the
    developer's own directory. It will not be stored in the addon repo and only be symlinked to the target Blender
    addon path as a directory symlink. It only supports a directory containing a __init__ file with bl_info in it.
    Note: the symlinked directory name will be the addon name extracted from the bl_info dictionary. This design allows
    the use of arbitrary directory names, such as "src" or "addon".
    """

    def __init__(self, addon_path: str or Path):
        """
        Create a BlenderDevDirectoryAddon object from the addon path.

        :param addon_path: a path to the addon, which must be a directory
        """
        super().__init__(addon_path)

    def _get_addon_init_file_content(self) -> str or None:
        files = list(self.data_path.iterdir())
        # Search for the single-file Python addon file at top level
        if len(files) == 1 and files[0].name.endswith('.py') and files[0].name != '__init__.py':
            self.is_single_file_addon = True
            addon_entry_file_path = files[0]
        # Search for the __init__.py file at top level
        elif '__init__.py' in [f.name for f in files]:
            self.is_single_file_addon = False
            addon_entry_file_path = self.data_path / '__init__.py'
        else:
            return None
        with open(addon_entry_file_path, encoding='utf-8') as f:
            return f.read()


class BlenderDevSingleFileAddon(BlenderDevAddon):
    """
    A class representing a Blender addon in development, which is a single file located in a non-repo path, typically
    the developer's own directory. The only format supported is a single .py file with Blender addon information in it,
    hence this class inherits from BlenderSingleFileAddon.
    """

    def __init__(self, addon_path: str or Path):
        """
        Create a BlenderDevDirectoryAddon object from the addon path.

        :param addon_path: a path to the addon, which must be a directory
        """
        super().__init__(addon_path)

    def _get_addon_init_file_content(self) -> str or None:
        with open(self.data_path, encoding='utf-8') as f:
            return f.read()


class BlenderAddonManager:
    """
    A statis class for creating BlenderAddon objects and other related functions falls outside the scope of the
    BlenderAddon class.
    """

    def __new__(cls, *args, **kwargs):
        raise Exception('This class should not be instantiated.')

    @staticmethod
    def _if_contain_addon_info(text_block: str) -> Result:
        """
        Use regular expression to search for the bl_info dictionary in the text block.

        :param text_block: a string containing the text to be searched

        :return: a Result object indicating if the bl_info dictionary is found
        """
        # "bl_info = { ... }" is required to define a valid Blender addon
        match = re.search(r'bl_info\s*=\s*{.*?}', text_block, re.DOTALL)
        if match:
            return Result(True, 'Addon info found')
        return Result(False, 'Addon info not found')

    @staticmethod
    def detect_addon_type(addon_path: str or Path) -> Result:
        """
        Detect the addon type based on the addon path. It will return a Result object with the detected addon type in
        its data field. If the addon type cannot be detected, the Result object will contain the error message.

        :param addon_path: a path to the addon, which can be a zip file, a directory, or a single Python file.

        :return: a Result object with the detected addon type in its data field
        """

        def get_zipped_file_content(zip_filestream: zipfile.ZipFile, in_zip_file: str) -> str:
            """
            Get the content of a file in a zip file.

            :param zip_filestream: a ZipFile object
            :param in_zip_file: a file path in the zip file

            :return: string content of the file
            """
            with zip_filestream.open(in_zip_file, 'r') as zf:
                return zf.read().decode('utf-8')

        addon_path = Path(addon_path)
        if addon_path.exists():
            if addon_path.is_file():
                # Zipped addon
                if addon_path.suffix == '.zip':
                    with (zipfile.ZipFile(addon_path, 'r') as z):
                        # Get non-directory files in the zip file
                        zipped_files = [name for name in z.namelist() if
                                        not name.endswith('/') and not name.endswith('\\')]
                        # Zipped single-file addon
                        if len(zipped_files) == 1 and zipped_files[0].endswith('.py') \
                                and not zipped_files[0].endswith('__init__.py'):
                            if BlenderAddonManager._if_contain_addon_info(get_zipped_file_content(z, zipped_files[0])):
                                return Result(True, 'Single-file zipped addon', BlenderZippedAddon)
                        # Zipped regular addon
                        else:
                            # Search for __init__ at top level
                            init_files = [name for name in z.namelist() if '/' not in name and '\\' not in name and
                                          name.endswith('__init__.py')]
                            # Search for __init__ one level down if not found at top level
                            if len(init_files) == 0:
                                init_files = [name for name in z.namelist()
                                              if (name.count('/') == 1 or name.count('\\') == 1)
                                              and name.endswith('__init__.py')]
                            if len(init_files) == 1:
                                if BlenderAddonManager._if_contain_addon_info(
                                        get_zipped_file_content(z, init_files[0])):
                                    return Result(True, 'Regular zipped addon', BlenderZippedAddon)
                    return Result(False, f'Addon info not found. Invalid addon file at {addon_path}.')
                # Single file addon
                elif addon_path.suffix == '.py':
                    with open(addon_path, encoding='utf-8') as f:
                        if BlenderAddonManager._if_contain_addon_info(f.read()):
                            return Result(True, 'Single-file addon', BlenderSingleFileAddon)
                    return Result(False, f'Addon info not found. Invalid addon file at {addon_path}.')
                else:
                    return Result(False, 'Invalid addon file type, must be a zip file or a Python file.')
            # Directory addon
            else:
                files = list(addon_path.iterdir())
                # Search for the single-file Python addon file at top level
                if len(files) == 1 and files[0].name.endswith('.py') and files[0].name != '__init__.py':
                    addon_entry_file_path = files[0]
                # Search for the __init__.py file at top level
                elif '__init__.py' in [f.name for f in files]:
                    addon_entry_file_path = addon_path / '__init__.py'
                else:
                    return Result(False, f'Addon info not found. Invalid addon directory at {addon_path}.')
                with open(addon_entry_file_path, encoding='utf-8') as f:
                    if BlenderAddonManager._if_contain_addon_info(f.read()):
                        return Result(True, 'Single-file directory addon', BlenderDirectoryAddon)
                return Result(False, f'Addon info not found. Invalid addon directory at {addon_path}.')
        return Result(False, f'Addon not found at {addon_path}.')

    @staticmethod
    def create_blender_addon(addon_path: str or Path) -> Result:
        """
        Create a BlenderAddon object from the addon path. It will automatically detect the addon type and use the
        corresponding subclass. It will return a Result object with the created BlenderAddon object in its data field.

        :param addon_path: a path to the addon, which can be a zip file, a directory, or a single Python file.

        :return: a Result object with the created BlenderAddon object in its data field
        """
        addon_path = Path(addon_path)
        result = BlenderAddonManager.detect_addon_type(addon_path)
        if result:
            blog(2, f'Creating a {result.data.__name__} instance...')
            addon_class = result.data
            return addon_class(addon_path).create_instance()
        else:
            return result

    @staticmethod
    def detect_dev_addon_type(addon_path: str or Path):
        """
        Detect the dev addon type based on the addon path. It will return a Result object with the detected addon type
        in its data field. If the dev addon type cannot be detected, the Result object will contain the error message.

        :param addon_path: a path to the addon, which can only be a directory or a single Python file.

        :return: a Result object with the detected dev addon type in its data field
        """
        addon_path = Path(addon_path)
        if addon_path.exists():
            # Single-file dev addon
            if addon_path.is_file() and addon_path.suffix == '.py':
                with open(addon_path, encoding='utf-8') as f:
                    if BlenderAddonManager._if_contain_addon_info(f.read()):
                        return Result(True, 'Dev single-file addon', BlenderDevSingleFileAddon)
                return Result(False, f'Dev addon info not found. Invalid dev addon file at {addon_path}.')
            # Directory addon
            else:
                # Search for the __init__.py file at top level
                init_files = [f for f in list(addon_path.iterdir()) if f.name == '__init__.py']
                if len(init_files) == 1:
                    with open(init_files[0], encoding='utf-8') as f:
                        if BlenderAddonManager._if_contain_addon_info(f.read()):
                            return Result(True, 'Dev directory addon', BlenderDevDirectoryAddon)
                return Result(False, f'Dev addon info not found. Invalid addon directory at {addon_path}.')
        return Result(False, f'Dev addon not found at {addon_path}.')

    @staticmethod
    def create_blender_dev_addon(addon_path: str or Path) -> Result:
        """
        Create a dev BlenderAddon object from the addon path. It will automatically detect the dev addon type and use
        the corresponding subclass. It will return a Result object with the created BlenderAddon object in its data
        field. Note: user needs to call this method explicitly to create a dev addon, since some type of addon path can
        be created a BlenderDirectoryAddon object or a BlenderSingleFileAddon object, which is not a dev addon.

        :param addon_path: a path to the addon, which can be a zip file, a directory, or a single Python file.

        :return: a Result object with the created BlenderAddon object in its data field
        """
        addon_path = Path(addon_path)
        result = BlenderAddonManager.detect_dev_addon_type(addon_path)
        if result:
            blog(2, f'Creating a {result.data.__name__} instance...')
            addon_class = result.data
            return addon_class(addon_path).create_instance()
        else:
            return result
