from pathlib import Path
import shutil

from commons.common import Dillable, SharedFunctions as SF


class BlenderScript(Dillable):

    def __init__(self, script_path, repo_dir=None, delete_existing=False):
        super().__init__()
        self.script_path = Path(script_path)
        if script_path.exists() and script_path.is_file() and script_path.suffix == '.py':
            self.name = self.script_path.stem
            if repo_dir:
                self._store_in_repo(repo_dir, delete_existing=delete_existing)
        else:
            raise FileNotFoundError(f'Valid Blender script not found at {self.script_path}')

    def _store_in_repo(self, repo_dir, delete_existing=False):
        repo_addon_path = Path(repo_dir) / self.script_path.name
        SF.ready_target_path(repo_addon_path, ensure_parent_dir=True, delete_existing=delete_existing)
        shutil.copy(self.script_path, repo_addon_path)
        if repo_addon_path.exists():
            self.addon_path = repo_addon_path
        else:
            raise Exception(f'Error copying addon to {repo_addon_path}')

    def verify(self) -> bool:
        return self.script_path.exists()

    def compare_content(self, other) -> bool:
        """
        Compare the content of this script with another script. This is often called for the purpose of updating the
        script in the repository.
        :param other:
        :return:
        """
        if issubclass(other.__class__, BlenderScript):
            return self.name == other.name
        return False

    def __eq__(self, other):
        return super().__eq__(other) and self.addon_path == other.addon_path

    def __hash__(self):
        return hash(self.script_path)


class BlenderRegularScript(BlenderScript):
    def __init__(self, script_path, repo_dir=None, delete_existing=False):
        super().__init__(script_path, repo_dir=repo_dir, delete_existing=delete_existing)

    def __str__(self):
        return f'Regular Script: {self.name}'


class BlenderStartupScript(BlenderScript):
    def __init__(self, script_path, repo_dir=None, delete_existing=False):
        super().__init__(script_path, repo_dir=repo_dir, delete_existing=delete_existing)

    def __str__(self):
        return f'Startup Script: {self.name}'
