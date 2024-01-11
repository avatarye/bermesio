from pathlib import Path
import shutil
import sys

from commons.common import Dillable, Result, SharedFunctions as SF
from config import Config


class Component(Dillable):

    def __init__(self, data_path: str or Path):
        super().__init__()
        self.name = 'Unnamed Component'
        self.data_path = None  # Absolute data path this component is associated with. Can be external or in-repo.
        self.source_path = None  # Absolute data path this component is created from.
        self.repo_rel_path = None  # Relative path to this component's associated data stored in the repo if any.
        self.if_store_in_repo = False  # If the data of this component can be stored in the repo.
        self.is_stored_in_repo = False  # If the data of this component is stored in the repo.
        self.platform = sys.platform  # OS platform
        self.dill_extension = '.dil'
        self._hash = None  # Unique identifier of the component data based on the data itself, not this instance.
        self.init_params = {}  # Parameters used to initialize this instance.

        # Perform a preliminary check on data_path and set the paths
        data_path = Path(data_path)
        if data_path.exists():
            # If the data path is inside the repo, this component is initialized from existing data in the repo.
            if Config.repo_dir in data_path.parents:
                self.data_path = data_path
                self.source_path = None
                self.repo_rel_path = data_path.relative_to(Config.repo_dir)
                self.if_store_in_repo = True
                self.is_stored_in_repo = True
            else:
                # If the data path is outside the repo, this component is initialized from external data.
                self.data_path = data_path
                self.source_path = data_path
                self.repo_rel_path = None
        else:
            self.data_path = None

    def create_instance(self) -> Result:
        raise NotImplementedError  # Force the subclass to implement this method.

    def store_in_repo(self, repo_dir: str or Path) -> Result:
        """
        Store the data of this component in the repo.

        :param repo_dir: a str or Path object of the path to the repo directory where the data will be stored

        :return: a Result object indicating if the storing is successful
        """
        if self.if_store_in_repo:
            if Config.repo_dir not in self.data_path.parents:
                repo_path = Path(repo_dir) / self.name
                result = SF.ready_target_path(repo_path)
                if not result:
                    return result
                try:
                    if self.data_path.is_file():
                        shutil.copy(self.data_path, repo_path)
                    else:
                        shutil.copytree(self.data_path, repo_path)
                except OSError:
                    pass
                # If successfully stored in the repo, update related attributes.
                if repo_path.exists():
                    self.data_path = repo_path
                    self.repo_rel_path = self.data_path.relative_to(Config.repo_dir)
                    self.is_stored_in_repo = True  # Flag it is already stored in the repo
                    return Result(True)
                return Result(False, f'Error storing data to {repo_path}')
            else:
                return Result(False, f'Error storing data to {repo_dir}: already in the repo')
        else:
            return Result(False, f'Error storing data to {repo_dir}: not allowed')
