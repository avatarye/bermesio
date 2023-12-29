import ast
from pathlib import Path
import re
import zipfile

from packaging.version import Version

from commons.common import blog


class BlenderAddon:

    def __init__(self, addon_path, copy_to_repo_path=None):
        self.addon_path = Path(addon_path)
        if self.addon_path.exists():
            self.name, self.version, self.blender_version, self.description = self._get_addon_info()
            # All the information must be available to be a valid Blender addon
            if None not in [self.name, self.version, self.blender_version, self.description]:
                if copy_to_repo_path:
                    self._copy_to_repo()
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

    def _copy_to_repo(self):
        pass


class BlenderZippedAddon(BlenderAddon):
    """
    A class representing a Blender addon in a zip file with necessary information, including the addon name, version,
    Blender version, and description.
    """

    def __init__(self, addon_path):
        super().__init__(addon_path)

    def _get_addon_init_file_content(self) -> str or None:
        with zipfile.ZipFile(self.addon_path, 'r') as z:
            for file in z.namelist():
                if file.count('/') == 1 and file.endswith('__init__.py'):
                    with z.open(file) as f:
                        content = f.read()
                        return content.decode('utf-8')
        return None


class BlenderDirectoryAddon(BlenderAddon):
    """
    A class representing a Blender addon in a directory with necessary information, including the addon name, version,
    Blender version, and description.
    """

    def __init__(self, addon_path):
        super().__init__(addon_path)

    def _get_addon_init_file_content(self) -> str or None:
        addon_init_path = self.addon_path / '__init__.py'
        if addon_init_path.exists():
            with open(addon_init_path, encoding='utf-8') as f:
                return f.read()
        return None
