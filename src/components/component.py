import hashlib
from pathlib import Path
import shutil
import sys

from commons.common import Dillable, Result, SharedFunctions as SF
from config import Config


class Component(Dillable):

    dill_extension = '.dil'  # Extension of the dill file

    def __init__(self, data_path: str or Path):
        super().__init__()
        self.name = 'Unnamed Component'
        self.data_path = None  # Absolute data path this component is associated with. Can be external or in-repo.
        self.source_path = None  # Absolute data path this component is created from.
        self.repo_rel_path = None  # Relative path to this component's associated data stored in the repo if any.
        self.if_store_in_repo = False  # If the data of this component can be stored in the repo.
        self.is_stored_in_repo = False  # If the data of this component is stored in the repo.
        self.is_renamable = False  # If the data of this component can be renamed
        self.is_upgradeable = False  # If the data of this component can be upgraded (comparing version and replace)
        self.is_duplicable = False  # If the data of this component can be duplicated (copy and paste)
        self.platform = sys.platform  # OS platform
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
                if self.data_path.is_dir():
                    repo_path = Path(repo_dir) / self.name  # Use the component name as the directory name
                else:
                    repo_path = Path(repo_dir) / self.data_path.name  # Preserve the original file name
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

    def verify(self) -> bool:
        """
        Verify if this Component object is valid by checking if the data path exists.

        :return: True if the data path is valid, otherwise False
        """
        # If the data is stored in the repo, use repo relative path to check if the data exists in the repo. This is to
        # enable loading data from a repo that has been moved to another location.
        if self.is_stored_in_repo and self.repo_rel_path is not None:
            data_path = Config.repo_dir / self.repo_rel_path
            if data_path.exists():
                self.data_path = data_path
        return self.data_path.exists()

    def __eq__(self, other) -> bool:
        """
        The equality of 2 Component instances is determined by the platform and the data path.

        :param other: another Component object

        :return: True if the platform and data path of this instance is the same as the other instance, otherwise False
        """
        if issubclass(other.__class__, Component):
            # Compare repo relative path if stored in repo
            if self.is_stored_in_repo and self.repo_rel_path is not None:
                return self.repo_rel_path == other.repo_rel_path
            return self.data_path == other.data_path
        return False

    @staticmethod
    def get_stable_hash(string: str) -> int:
        """
        Get a stable hash of the object which will be used to compare again sub-repo pool. The hash will be a
        representation of a core string of the object, which is usually the path of the associated data. Due to the
        integer overflow issue, the hash is sliced every 5 characters and converted to integer.
        """
        return int(hashlib.sha256(string.encode()).hexdigest()[::5], 16)

    def __hash__(self):
        """
        The hash of a Component instance is determined by the data path. The hash value is a sha256 hash of the data
        path sliced every 5 characters and converted to integer.

        :return: a hash value of the data path
        """
        # If the data is stored in the repo, use the repo relative path to get the hash. This is to enable establishing
        # inter-dependency between components in a repo that has been moved to another location.
        if self.is_stored_in_repo and self.repo_rel_path is not None:
            return self.get_stable_hash(self.repo_rel_path.as_posix())
        return self.get_stable_hash(self.data_path.as_posix())
