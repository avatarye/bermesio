import hashlib
from pathlib import Path
import shutil
import sys
import uuid

import dill
import packaging.version

from commons.common import Result, SharedFunctions as SF, blog, SharedFunctions
from config import Config


class Dillable:
    """
    A base class that has dill related functions.
    """

    dill_extension = '.dil'

    @property
    def status_dict(self):
        return self._get_status_dict()

    def __init__(self):
        self.saved_app_version: packaging.version.Version = Config.app_version
        self.uuid = uuid.uuid4().hex
        self.dill_extension = '.dil'  # This will be overriden by subclasses
        self.dill_save_dir = None  # This will be set by the repo class
        self.dill_save_path = None  # This is the last saved dill file path

    def save_to_disk(self) -> Result:
        """
        Save the object to disk as a dill file. The save file is named after the hash of the object with a specific
        extension depending on the subclass. All subclasses should have the dill_extension attribute overridden by
        the Depository class during initialization. All subclasses should have __hash__ implemented.

        :return: a Result object
        """
        if self.dill_save_dir is not None:
            self.dill_save_path = Path(self.dill_save_dir) / f'{str(hash(self)).zfill(16)}{self.dill_extension}'
            with open(self.dill_save_path, 'wb') as pickle_file:
                self.saved_app_version = Config.app_version
                try:
                    dill.dump(self, pickle_file)
                    return Result(True, f'{self.__class__.__name__} saved to {self.dill_save_path}')
                except Exception as e:
                    return Result(False, f'Error saving {self.__class__.__name__} to {self.dill_save_path}: {e}')
        else:
            return Result(False, f'Error saving {self.__class__.__name__} to {self.dill_save_path}: save_dir not set')

    def save_dill(fn) -> Result:
        """
        A decorator that saves the object to disk as a dill file after the function call.

        :return: a Result object
        """
        def wrapper(self, *args, **kwargs):
            result = fn(self, *args, **kwargs)
            if result:
                if self.dill_save_dir is not None:  # Only save if the dill_save_dir is set
                    save_result = self.save_to_disk()
                    if not save_result:
                        return save_result
                return result
        return wrapper

    @classmethod
    def load_from_disk(cls, file_path: str or Path) -> Result:
        """
        Load the dill file from disk, run its verification function and return the loaded instance.

        :param file_path: the path of the dill file

        :return: a Result object, the data field contains the loaded instance if successful
        """
        file_path = Path(file_path)
        if file_path.exists() and file_path.is_file():
            with open(file_path, 'rb') as pickle_file:
                loaded_instance = dill.load(pickle_file)
            # Compare version
            if loaded_instance.saved_app_version != Config.app_version:
                blog(3, f'Dill file saved with a different version {loaded_instance.saved_app_version}.')
            # Verify the loaded instance
            if loaded_instance.verify():
                loaded_instance.is_verified = True
                return Result(True, f'{loaded_instance.__class__.__name__} restored from {file_path}', loaded_instance)
            else:
                loaded_instance.is_verified = False
                return Result(True, f'Verification failed for {loaded_instance.__class__.__name__} restored from '
                                    f'{file_path}', loaded_instance)  # Still return the loaded instance
        else:
            return Result(False, f'Dill file not found: {file_path}', file_path)

    def remove_from_disk(self):
        """Remove the dill file from disk."""
        if self.dill_save_path and self.dill_save_path.exists():
            SharedFunctions.remove_target_path(self.dill_save_path)

    def _get_status_dict(self):
        return {}

    def verify(self) -> bool:
        """Verify the object, mainly called after restoration. Actual implementation is in the subclass."""
        raise NotImplementedError

    def compare_uuid(self, other: 'Dillable') -> bool:
        """Compare the UUID of the object with another Dillable object."""
        return self.uuid == other.uuid


class Component(Dillable):

    dill_extension = '.dil'  # Extension of the dill file

    is_renamable = False  # If the data of this component can be renamed
    is_upgradeable = False  # If the data of this component can be upgraded (comparing version and replace)
    is_duplicable = False  # If the data of this component can be duplicated (copy and paste)
    is_editable = False # If the data of this component can be edited (open in the editor widget)

    def __init__(self, data_path: str or Path):
        super().__init__()
        self.name = 'Unnamed Component'
        self.data_path = None  # Absolute data path this component is associated with. Can be external or in-repo.
        self.source_path = None  # Absolute data path this component is created from.
        self.repo_rel_path = None  # Relative path to this component's associated data stored in the repo if any.
        self.if_store_in_repo = False  # If the data of this component can be stored in the repo.
        self.is_stored_in_repo = False  # If the data of this component is stored in the repo.
        self.platform = sys.platform  # OS platform
        self.init_params = {}  # Parameters used to initialize this instance.

        # Perform a preliminary check on data_path and set the paths
        if data_path is not None:  # Some pure configuration class, like Profile, does not have data path
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
                    self.source_path = self.data_path
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
        # interdependency between components in a repo that has been moved to another location.
        if self.is_stored_in_repo and self.repo_rel_path is not None:
            return self.get_stable_hash(self.repo_rel_path.as_posix())
        return self.get_stable_hash(self.data_path.as_posix())
