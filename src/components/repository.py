import os
from pathlib import Path
import tempfile

import requests

from commons.common import Result, blog
from commons.command import run_command
from components.manager import ObjectPool, pooled_class
from components.blender_addon import BlenderZippedAddon, BlenderDirectoryAddon
from components.blender_program import BlenderProgram
from components.blender_venv import BlenderVenv
from components.profile import Profile
from config import Config


@pooled_class
class Repository:

    def __init__(self, repository_path=None):
        # Allow using a repository path other than the default one
        if repository_path:
            self.repository_path = Path(repository_path)
        else:
            self.repository_path = Path(Config.repository_path)
        self.is_repository_path_ready = False
        self.has_internet_connection = False
        self.verify_readiness()

        # Initialize the sub-repositories
        self.profile_repo = self._get_profile_repo()
        self.blender_program_repo = self._get_blender_program_repo()
        self.blender_addon_repo = self._get_blender_addon_repo()
        self.blender_script_repo = self._get_blender_script_repo()

    def _is_repository_path_ready(self) -> bool:
        try:
            # Check if the path exists and is a directory
            if not self.repository_path.exists():
                os.makedirs(self.repository_path)
            if os.path.exists(self.repository_path) and self.repository_path.is_dir():
                testfile = tempfile.TemporaryFile(dir=self.repository_path)
                testfile.close()
                return True
        except (OSError, IOError):
            pass
        blog(5, f'Repository path {self.repository_path} is not accessible.')
        return False

    @staticmethod
    def _if_has_internet_connection() -> bool:
        try:
            response = requests.get("http://www.google.com", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            pass
        blog(3, f'No internet connection.')
        return False

    def verify_readiness(self):
        self.is_repository_path_ready = self._is_repository_path_ready()
        self.has_internet_connection = self._if_has_internet_connection()

    def _get_profile_repo(self) -> dict:
        return {}

    def _get_blender_program_repo(self) -> dict:
        return {}

    def _get_blender_addon_repo(self) -> dict:
        return {}

    def _get_blender_script_repo(self) -> dict:
        return {}

    def verify_sub_repos(self):
        return {}
