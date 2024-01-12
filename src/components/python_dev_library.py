import os
from pathlib import Path

from commons.common import Result, blog, SharedFunctions as SF
from components.component import Component


class PythonDevLibrary(Component):
    """
    A class representing a development Python library. It uses the actual source code directory which will be symlinked
    to the deploy directory. It is a simplified approach appending a local library to the target Python environment
    without involving more complex build process or package set up. It is suitable for linking small libraries to the
    Blender dev environment.
    """

    def __init__(self, library_path: str or Path, name: str = None):
        """
        Create a PythonDevLibrary object with a custom name if supplied.

        :param library_path: a str or Path object of the path to the development library source code
        :param name: a custom name of the development library, especially when the library name is not a unique
                             name such as "src" or "source". The symlink will use this name as the deployed name.
        """
        super().__init__(library_path)
        self.dill_extension = '.dpl'
        self.if_store_in_repo = False
        self.init_params = {'library_path': library_path, 'name': name}

    def create_instance(self) -> Result:
        """
        Create a PythonDevLibrary object based on an existing development library source code path.

        :return: a Result object indicating if the initialization is successful, the message generated during the
                 initialization, and this object if successful.
        """
        if self.data_path is not None:
            self.name = self.init_params['name']
            if self.name is None:  # If no custom name is supplied, use the name of the library path.
                self.name = self.data_path.name
            if not SF.is_valid_name_for_path(self.name):
                return Result(False, f'Invalid name {self.name} for the Python development library.')
            return Result(True, 'Python development library instance created successfully', self)
        else:
            return Result(False, f'Python development library path not found at {self.data_path}')

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
                os.symlink(self.data_path, deployed_target_path)
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
                                 f'{self.data_path}')

    def __str__(self):
        return f'{self.__class__.__name__}: {self.name}'


class PythonDevLibraryManager:
    """
    A statis class for creating PythonDebLibrary objects and other related functions falls outside the scope of the
    PythonDebLibrary class.
    """

    def __new__(cls, *args, **kwargs):
        raise Exception('This class should not be instantiated.')

    @staticmethod
    def create(library_path: str or Path, name: str = None) -> Result:
        """
        Create a development PythonDevLibrary object with a custom name if supplied. It will return a Result object 
        indicating whether the creation is successful with the PythonDevLibrary object as the data if successful.

        :param library_path: a str or Path object of the path to the development library source code
        :param name: a custom name of the development library, especially when the library name is not a unique
               name such as "src" or "source"

        :return: a Result object indicating whether the creation is successful with the PythonDevLibrary object as the
                 data if successful
        """
        blog(2, 'Creating a Python development library instance...')
        return PythonDevLibrary(library_path, name=name).create_instance()
