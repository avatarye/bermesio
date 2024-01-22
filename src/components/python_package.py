import packaging.version
from pathlib import Path
import requests

from commons.common import blog


class PythonPackage:
    """ A base class representing a Python package with essential information. """
    def __init__(self):
        self.name = None
        self.version = None
        self.summary = None

    def get_installation_str(self, with_version=True) -> str:
        """
        Get the installation string for this package, which is in the format of 'package_name==package_version'. It also
        handles name or version being None.

        :param with_version: a boolean indicating whether to include the version in the installation string
        :return: a string of the installation string
        """
        if self.name is not None:
            if with_version and self.version is not None:
                return f'{self.name}=={self.version}'
            else:
                return self.name
        else:
            return ''

    def __str__(self):
        return (f'{self.name if self.name is not None else "unknown"}'
                f'=={self.version if self.version is not None else "unknown"}')


class PythonLocalPackage(PythonPackage):

    def __init__(self, local_package_path: str or Path):
        """
        Initialize a PythonLocalPackage from a local package path. The local package path should be a directory of a
        package installed in any path. The package name and version will be retrieved from the metadata file.

        :param local_package_path: a string or Path of the local package path
        """
        super().__init__()
        self.local_package_path = Path(local_package_path)
        if self.local_package_path.exists():
            self.import_path = self.local_package_path.parent  # The path to import the package
            self.metadata = self._get_package_metadata()
            if self.metadata is not None:
                try:
                    self.name = self.metadata['name']
                    self.version = packaging.version.parse(self.metadata['version'])
                    self.summary = self.metadata.get('summary', 'Unknown')
                    # if 'requires-python' in self.metadata:
                    #     self.required_python = packaging.version.parse(self.metadata['requires-python'])
                    # else:
                    #     self.required_python = None
                except KeyError:
                    raise KeyError(f'Incorrect metadata file for {self.local_package_path}')
            else:
                raise FileNotFoundError(f'Metadata file not found for {self.local_package_path}')
        else:
            raise FileNotFoundError(f'Local package not found at {self.local_package_path}')

    def _get_package_metadata(self) -> dict or None:
        """
        Get the metadata of a package installed in at a specified path.

        :return: a dictionary of the metadata or None if not found
        """
        # Search for dist-info or egg-info directories
        package_name = self.local_package_path.name
        info_dir = (list(self.local_package_path.parent.glob(f'{package_name}-*.dist-info'))
                    + list(self.local_package_path.parent.glob(f'{package_name}-*.egg-info')))
        if len(info_dir) == 1:
            info_dir = info_dir[0]
            # Search for metadata file
            metadata_path = info_dir / 'METADATA'
            if not metadata_path.exists():
                metadata_path = info_dir / 'PKG-INFO'
            if metadata_path.exists() and metadata_path.is_file():
                with open(metadata_path, 'r', encoding='utf-8') as metadata_file:
                    metadata = metadata_file.readlines()
                    metadata_dict = {}
                    for line in metadata:
                        if line == '\n':
                            break
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key, value = key.strip().lower(), value.strip()
                            # Only the first occurrence of the key will be kept, which is the desired data.
                            if key not in metadata_dict:
                                metadata_dict[key] = value
                    return metadata_dict
            else:
                blog(3, f'Metadata file not found for {package_name}.')
                return None
        else:
            blog(3, f'No dist-info or egg-info directory found for {package_name}.')
            return None


class PythonPyPIPackage(PythonPackage):
    """
    A class representing a Python package from PyPI with name and package version. Further information can be retrieved
    from PyPI. This is mainly used for installing packages from PyPI.
    """
    def __init__(self, name_version_str: str, get_pypi_info=False):
        """
        Initialize a PythonPyPIPackage from a string of package name and version. The package name and version will be
        retrieved from the string. Further information can be retrieved from PyPI if argument get_pypi_info is True.

        :param name_version_str: a string of package name and version in the format of 'package_name==package_version'
        :param get_pypi_info: a boolean indicating whether to retrieve further information from PyPI
        """
        super().__init__()
        self.name, self.version = self._get_name_version_from_str(name_version_str)
        self.summary = None
        self.is_found_on_pypi, self.pypi_info = None, None  # is_found_on_pypi is None if not checked
        if get_pypi_info:
            self.gen_pypi_info()

    @staticmethod
    def _get_name_version_from_str(name_version_str: str) -> (str, packaging.version.Version):
        """
        Parse name_version_str to get name and version.

        :param name_version_str: accepts 'package_name==package_version' or 'package_name' format. The former is the
        format of the output of 'pip freeze'. The latter is name only.

        :return: a tuple of name and version
        """
        # Local package format is not supported.
        if '@ file:///' in name_version_str:
            blog(3, f'Local package string format, {name_version_str}, is not supported.')
            return None, None
        # This is the standard format of 'pip freeze'
        elif '==' in name_version_str:
            segments = name_version_str.rstrip().split('==')
            return segments[0].lstrip(), packaging.version.parse(segments[1])
        # This is a string with only name, mostly used for making query to PyPI
        elif ' ' not in name_version_str:
            return name_version_str, None
        # All other formats are not supported
        blog(3, f'Incorrect package format, {name_version_str}.')
        return None, None

    def gen_pypi_info(self):
        """
        Generate a dictionary of PyPI information for the package, including the latest version and the description.
        """
        api_url = f"https://pypi.org/pypi/{self.name}/json"
        response = requests.get(api_url)
        if response.status_code == 200:
            package_info = response.json()
            if 'info' in package_info:
                self.is_found_on_pypi = True
                self.pypi_info = package_info['info']
                self.summary = self.pypi_info.get('summary', None)
                return
        self.is_found_on_pypi, self.pypi_info = False, None


class PythonPackageSet:
    """
    A class representing a set of Python packages, which is usually installed in Python environment. It can also be
    used to represent a set of Python packages for further installation, which is the reason why 2 arithmetic operators
    are implemented for easy calculation of the union and difference of two PythonPackageSets.
    """
    def __init__(self, package_set_input: str or Path):
        """
        Initialize a PythonPackageSet from a string of packages or a directory of packages. The string of packages is
        usually the output of 'pip freeze'. The directory of packages is usually the site-packages directory of a Python
        environment.

        :param package_set_input: a string of packages or a Path of the directory of packages
        """
        # When package_set_input is empty, create an empty package set as a container
        if package_set_input == '':
            self.package_dict = {}
        # When package_set_input is a Path, it is a directory of packages
        elif isinstance(package_set_input, Path):
            self.package_dict = self._get_package_dict_from_path(package_set_input)
        # When package_set_input is a string, try to parse it as a string of packages or a directory of packages
        else:
            package_set_path = Path(package_set_input)
            if package_set_path.exists():
                if package_set_path.is_dir():
                    self.package_dict = self._get_package_dict_from_path(package_set_path)
                else:
                    raise ValueError(f'Input {package_set_input} is not a directory.')
            else:
                self.package_dict = self._get_package_dict_from_str(package_set_input)

    @staticmethod
    def _get_package_dict_from_path(package_set_path: Path) -> dict:
        """
        Get a dictionary of PythonPackage objects from a directory of packages. The directory should contain

        :param package_set_path: a Path of the directory of packages

        :return: a dictionary of PythonPackage objects
        """
        # Search for dist-info or egg-info directories
        package_info_dirs = [child_dir for child_dir in package_set_path.iterdir()
                             if child_dir.is_dir() and ('dist-info' in child_dir.name or 'egg-info' in child_dir.name)]
        package_dirs = []
        # Search for the package directory according to the dist-info or egg-info directory
        for package_info_dir in package_info_dirs:
            package_dir = package_info_dir.parent / package_info_dir.name.split('-', 1)[0]
            if package_dir.exists():
                package_dirs.append(package_dir)
        # Create a list of PythonPackage objects from the package directories
        package_list = [PythonLocalPackage(package_dir) for package_dir in package_dirs]
        return {package.name: package for package in package_list if package.name}  # Filter out invalid ones

    @staticmethod
    def _get_package_dict_from_str(packages_str) -> dict:
        """
        Get a dictionary of PythonPackage objects from a string of packages, which is usually the output of
        'pip freeze'.

        :param packages_str: a string of packages, each package is in the format of 'package_name==package_version'.

        :return: a dictionary of PythonPackage objects
        """
        package_list = [PythonPyPIPackage(package_str.strip()) for package_str in packages_str.strip().split('\n')]
        return {package.name: package for package in package_list if package.name}  # Filter out invalid ones

    def add_package(self, package: PythonPackage):
        """
        Add a PythonPackage to the package set.

        :param package: a PythonPackage object
        """
        self.package_dict[package.name] = package

    def remove_package(self, package: str or PythonPackage):
        """
        Remove a PythonPackage from the package set.

        :param package: a PythonPackage object
        """
        if isinstance(package, str):
            if package in self.package_dict:
                self.package_dict.pop(package)
        elif isinstance(package, PythonPackage):
            if package.name in self.package_dict:
                self.package_dict.pop(package.name)
        else:
            raise TypeError(f'Input {package} is not a PythonPackage.')

    def get_installation_str(self) -> str:
        """
        Get the installation string for the package set, which is in the format of 'package_name==package_version
        package_name==package_version ...'.

        :return: a string of the installation string for the contained packages
        """
        return ' '.join([package.get_installation_str() for package in self.package_dict.values()])

    def __add__(self, other: 'PythonPackageSet') -> 'PythonPackageSet':
        """
        Get the union of two package collections, with the version of the package being the latest of the two.

        :param other: the other PythonPackageSet to be added

        :return: a new PythonPackageSet with the union of the two PythonPackageSets
        """
        added_package_set = PythonPackageSet('')
        all_packages = list(self.package_dict.values()) + list(other.package_dict.values())
        while all_packages:
            package = all_packages.pop()
            if package.name in added_package_set.package_dict:
                if package.label_type > added_package_set.package_dict[package.name].label_type:
                    added_package_set.package_dict[package.name] = package
            else:
                added_package_set.package_dict[package.name] = package
        return added_package_set

    def __sub__(self, other: 'PythonPackageSet') -> 'PythonPackageSet':
        """
        Get the difference of two package collections, with the version of the package being the latest of the two.
        Same packages with different versions will be considered as different packages.

        :param other: the other PythonPackageSet to be subtracted

        :return: a new PythonPackageSet with the difference of the two PythonPackageSets
        """
        subtracted_package_set = PythonPackageSet('')
        for package_name, package in self.package_dict.items():
            if package_name not in other.package_dict:
                subtracted_package_set.package_dict[package_name] = package
            else:
                # Same package but higher version will be preserved
                if package.label_type > other.package_dict[package_name].label_type:
                    subtracted_package_set.package_dict[package_name] = self.package_dict[package_name]
        return subtracted_package_set

    def __str__(self):
        return ' '.join([str(package) for package in self.package_dict.values()])