import os
from pathlib import Path

from commons.common import Result, Dillable, blog, SharedFunctions as SF


class PythonDevLibrary(Dillable):
    """
    A class representing a development Python library. It uses the actual source code directory which will be symlinked
    to the deploy directory. It is a simplified approach appending a local library to the target Python environment
    without involving more complex build process or package set up. It is suitable for linking small libraries to the
    Blender dev environment.
    """

    def __init__(self, library_path: str or Path, library_name: str = None):
        """
        Create a PythonDevLibrary object with a custom name if supplied.

        :param library_path: a str or Path object of the path to the development library source code
        :param library_name: a custom name of the development library, especially when the library name is not a unique
                             name such as "src" or "source". The symlink will use this name as the deployed name.
        """
        super().__init__()
        self.library_path = Path(library_path)
        if self.library_path.exists():
            if library_name is None:  # If no custom name is supplied, use the name of the library path.
                library_name = self.library_path.name
            self.name = self._get_validated_library_name(library_name)
        else:
            raise FileNotFoundError(f'Development library path {self.library_path} does not exist.')

    @staticmethod
    def _get_validated_library_name(name: str) -> str:
        """
        Validate the library name. It should be a valid name for a path.

        :param name: a str of the library name
        :return: a str of the validated library name
        """
        if SF.is_valid_name_for_path(name):
            return name
        else:
            raise ValueError(f'Invalid library name {name}')

    def deploy(self, deploy_dir: str or Path, delete_existing=False) -> Result:
        """
        Deploy the development library to the deploy directory as a symlink.

        :param deploy_dir: a str or Path object of the path to the deploy directory
        :param delete_existing: a flag indicating whether to delete the existing symlink if exists

        :return: a Result object indicating whether the deployment is successful
        """
        deploy_dir = Path(deploy_dir)
        if self.verify():
            deployed_target_path = deploy_dir / self.name
            result = SF.ready_target_path(deployed_target_path, delete_existing=delete_existing)
            if not result:
                return result
            try:
                os.symlink(self.library_path, deployed_target_path)
            except OSError:
                return Result(False, f'Error creating symlink to development library at {deployed_target_path}. If '
                                     f'you are using Windows, please try again with administrator privilege.')
            if deployed_target_path.exists():
                blog(2, f'Symlinked development library {self.name} to {deployed_target_path}')
                return Result(True)
            else:
                return Result(False, f'Error creating symlink to development library at {deployed_target_path}.')
        else:
            return Result(False, f'Error symlinking development library {self.name}. The library not found at '
                                 f'{self.library_path}')

    def verify(self) -> Result:
        """
        Verify whether the development library path exists.

        :return: a Result object indicating whether the verification is successful
        """
        if self.library_path.exists():
            return Result(True)
        else:
            return Result(False, f'Development library path {self.library_path} does not exist.')

    def __str__(self):
        return f'{self.__class__.__name__}: {self.name}'

    def __eq__(self, other: 'PythonDevLibrary'):
        """
        The equality of 2 PythonDevLibrary objects is determined by the addon path instead of the instance itself. If the
        instance equality is required, use compare_uuid() from Dillable class.

        :param other: another PythonDevLibrary object

        :return: True if the libray path of this instance is the same as the other instance, otherwise False
        """
        if issubclass(other.__class__, PythonDevLibrary):
            return self.library_path == other.library_path
        return False

    def __hash__(self):
        return hash(self.library_path.as_posix())


class PythonDevLibraryManager:
    """
    A statis class for creating PythonDebLibrary objects and other related functions falls outside the scope of the
    PythonDebLibrary class.
    """

    def __new__(cls, *args, **kwargs):
        raise Exception('This class should not be instantiated.')

    @staticmethod
    def create_python_dev_library(library_path: str or Path, library_name: str = None) -> Result:
        """
        Create a development PythonDevLibrary object with a custom name if supplied. It will return a Result object 
        indicating whether the creation is successful with the PythonDevLibrary object as the data if successful.

        :param library_path: a str or Path object of the path to the development library source code
        :param library_name: a custom name of the development library, especially when the library name is not a unique
               name such as "src" or "source"

        :return: a Result object indicating whether the creation is successful with the PythonDevLibrary object as the
                 data if successful
        """
        library_path = Path(library_path)
        try:
            dev_lib = PythonDevLibrary(library_path, library_name=library_name)
            if dev_lib.verify():
                blog(2, 'Blender development library instance created successfully')
                return Result(True, 'Blender development library instance created successfully', dev_lib)
        except Exception as e:
            return Result(False, f'Error creating Blender development library instance: {e}', e)
