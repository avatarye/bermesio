import ast
from pathlib import Path
import re
import shutil
import zipfile

from packaging.version import Version

from commons.common import blog, Dillable, SharedFunctions as SF


class BlenderAddon(Dillable):
    """
    A class representing a Blender addon with necessary information, including the addon name, version, Blender version,
    and description. It supports the Blender addons packed in the following ways:
    1. A zip file containing a directory with a __init__.py file in it.
    2. A zip file containing __init__.py in it.
    3. A zip file containing one single python file with bl_info in it.
    4. A directory containing a __init__.py file in it.
    5. A directory containing one single python file with bl_info in it.
    6. One single python file with bl_info in it.
    Above formats will be handled by these 3 subclasses respectively, BlenderZippedAddon, BlenderDirectoryAddon, and
    BlenderSingleFileAddon. Each subclass will pack the addon to the addon repository using a unified zipped format as
    follows:
    - Non-single file addon:
     └ repository_path/addon.zip/addon_name/__init__.py
    - Single file addon:
      repository_path/addon.zip/addon_name.py
    Above zipped formats can be unpacked directly into the target Blender addon directory.
    """

    repo_name = 'Unknown Addon'
    deployed_dir_name = 'unknown_addon'
    repo_zip_file_name = 'unknown_addon.zip'

    def __init__(self, addon_path, repo_dir=None, delete_existing=False):
        super().__init__()
        self.addon_path = Path(addon_path)
        if self.addon_path.exists():
            self.name, self.version, self.blender_version_min, self.description = self._get_addon_info()
            # All the information must be available to be a valid Blender addon
            if None not in [self.name, self.version, self.blender_version_min, self.description]:
                # The name of the addon used in the repository GUI
                self.repo_name = f'{self.name}_{self.version}'
                # The name for the addon directory when deployed in Blender Addons path
                self.deployed_dir_name = self.name.replace(" ", "_").lower()
                # The name for the addon zip file stored in the repository
                self.repo_zip_file_name = self._get_repo_zip_file_name()
                if repo_dir:
                    self._store_in_repo(repo_dir, delete_existing=delete_existing)
            else:
                raise Exception(f'Error getting Blender addon information in {self.addon_path}')
        else:
            raise FileNotFoundError(f'Blender addon not found at {self.addon_path}')

    def _get_addon_init_file_content(self):
        return None

    def _get_addon_info(self) -> (str or None, Version or None, Version or None, str or None):
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
        blog(3, f'Error getting Blender addon information in {self.addon_path}')
        return None, None, None, None

    def _get_repo_zip_file_name(self) -> str:
        """
        Get a valid zip file name for the addon zip file stored in the repository.
        """
        return f'{self.repo_name.replace(" ", "_").lower()}.zip'

    def _store_in_repo(self, repo_dir, delete_existing=False):
        raise NotImplementedError

    def deploy(self, deploy_dir, delete_existing=False) -> bool:
        deploy_dir = Path(deploy_dir)
        if self.verify():
            deployed_dir = deploy_dir / self.deployed_dir_name
            if deployed_dir.exists():
                if delete_existing:
                    shutil.rmtree(deployed_dir)
                else:
                    raise FileExistsError(f'Addon already exists at {deployed_dir}')
            if not deployed_dir.exists():
                # Unzip this addon into the custom_addon_dir
                with zipfile.ZipFile(self.addon_path, 'r') as zip_ref:
                    zip_ref.extractall(deploy_dir)
            if deployed_dir.exists():
                return True
            else:
                raise Exception(f'Error deploying addon to {deploy_dir}')
        else:
            raise Exception(f'Error deploying addon to {deploy_dir}')

    def verify(self) -> bool:
        """
        Verify if the Blender addon path exists.
        """
        return self.addon_path.exists()

    def __str__(self):
        return f'Addon: {self.name}'


class BlenderZippedAddon(BlenderAddon):
    """
    A class representing a Blender addon in a zip file with necessary information, including the addon name, version,
    Blender version, and description.
    When packing the addon to the addon repository, it will handle 3 scenarios and pack the addon accordingly:
    """
    def __init__(self, addon_path, repo_dir=None, delete_existing=False):
        self.if_rezip = False
        super().__init__(addon_path, repo_dir=repo_dir, delete_existing=delete_existing)

    def _get_addon_init_file_content(self) -> str or None:
        with zipfile.ZipFile(self.addon_path, 'r') as z:
            found_addon_file = None
            # Detect if the zip file contains only one addon_name.py file at top level, which is one single file addon.
            top_level_files = [name for name in z.namelist() if '/' not in name and '\\' not in name]
            py_files = [name for name in top_level_files if name.endswith('.py') and not name.endswith('__init__.py')]
            if len(py_files) == 1:
                found_addon_file = py_files[0]
            # Look for __init__.py file in the zip file at top level or one level down.
            else:
                for file in z.namelist():
                    if file.count('/') == 0 and file.endswith('__init__.py'):
                        found_addon_file = file
                        self.if_rezip = True
                        break
                    if file.count('/') == 1 and file.endswith('__init__.py'):
                        found_addon_file = file
                        break
            if found_addon_file:
                with z.open(found_addon_file) as f:
                    content = f.read()
                    return content.decode('utf-8')
        return None

    def _store_in_repo(self, repo_dir, delete_existing=False):

        def rezip_with_top_dir(input_zip_path, output_zip_path, top_dir_name):
            with zipfile.ZipFile(input_zip_path, 'r') as zip_read:
                with zipfile.ZipFile(output_zip_path, 'w') as zip_write:
                    for item in zip_read.infolist():
                        data = zip_read.read(item.filename)
                        new_path = f"{top_dir_name}/{item.filename}"
                        zip_write.writestr(new_path, data)

        repo_addon_path = Path(repo_dir) / self.repo_zip_file_name
        SF.ready_target_path(repo_addon_path, ensure_parent_dir=True, delete_existing=delete_existing)
        # If the __init__.py file is found at top level, rezip the addon with a top level directory inserted.
        if self.if_rezip:
            rezip_with_top_dir(self.addon_path, repo_addon_path, self.deployed_dir_name)
        # If the __init__.py file is found one level down or a valid single python file addon, copy it to the repo.
        else:
            shutil.copy(self.addon_path, repo_addon_path)
        if repo_addon_path.exists():
            self.addon_path = repo_addon_path
        else:
            raise Exception(f'Error copying addon to {repo_addon_path}')


class BlenderDirectoryAddon(BlenderAddon):
    """
    A class representing a Blender addon in a directory with necessary information, including the addon name, version,
    Blender version, and description.
    When packing the addon to the addon repository, it will handle 2 scenarios and pack the addon accordingly:
    """

    def __init__(self, addon_path, repo_dir=None, delete_existing=False):
        self.addon_entry_file_path = None
        super().__init__(addon_path, repo_dir=repo_dir, delete_existing=delete_existing)

    def _get_addon_init_file_content(self) -> str or None:
        files = list(self.addon_path.iterdir())
        # If the addon directory contains only one python file, zip it directly.
        if len(files) == 1 and files[0].name.endswith('.py') and files[0].name != '__init__.py':
            self.addon_entry_file_path = files[0]
        elif '__init__.py' in [f.name for f in files]:
            self.addon_entry_file_path = self.addon_path / '__init__.py'
        else:
            return None
        with open(self.addon_entry_file_path, encoding='utf-8') as f:
            return f.read()

    def _store_in_repo(self, repo_dir, delete_existing=False):
        repo_addon_path = Path(repo_dir) / self.repo_zip_file_name
        SF.ready_target_path(repo_addon_path, ensure_parent_dir=True, delete_existing=delete_existing)
        if self.addon_entry_file_path:
            # If the addon directory contains __init__.py, zip it with a top level directory inserted.
            if self.addon_entry_file_path.name == '__init__.py':
                with zipfile.ZipFile(repo_addon_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for item in self.addon_path.glob('**/*'):
                        if item.is_file():
                            zipf.write(item, arcname=f'{self.deployed_dir_name}/{item.relative_to(self.addon_path)}')
            # If the addon directory contains only one python file, zip it directly.
            else:
                files = [f.name for f in self.addon_path.iterdir()]
                with zipfile.ZipFile(repo_addon_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(self.addon_path / files[0], arcname=files[0])
            if repo_addon_path.exists():
                self.addon_path = repo_addon_path
        else:
            raise Exception(f'Error copying addon to {repo_addon_path}')


class BlenderSingleFileAddon(BlenderAddon):
    """
    A class representing a Blender addon in a single python file with necessary information, including the addon name,
    version, Blender version, and description.
    """

    def __init__(self, addon_path, repo_dir=None, delete_existing=False):
        super().__init__(addon_path, repo_dir=repo_dir, delete_existing=delete_existing)

    def _get_addon_init_file_content(self) -> str or None:
        with open(self.addon_path, encoding='utf-8') as f:
            return f.read()

    def _store_in_repo(self, repo_dir, delete_existing=False):
        repo_addon_path = Path(repo_dir) / self.repo_zip_file_name
        SF.ready_target_path(repo_addon_path, ensure_parent_dir=True, delete_existing=delete_existing)
        with zipfile.ZipFile(repo_addon_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(self.addon_path, arcname=self.addon_path.name)
        if repo_addon_path.exists():
            self.addon_path = repo_addon_path
        else:
            raise Exception(f'Error copying addon to {repo_addon_path}')

