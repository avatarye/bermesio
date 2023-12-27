import packaging.version
from pathlib import Path
import requests


class PythonPackage:
    """
    A class representing a Python package with name and package version. Further information will be retrieved from
    PyPI.
    """
    def __init__(self, name_version_str, get_pypi_info=False):
        self.name, self.version = self._get_name_version_from_str(name_version_str)
        if get_pypi_info:
           self.gen_pypi_info()

    def _get_name_version_from_str(self, name_version_str) -> (str, packaging.version.Version):
        """
        Parse name_version_str to get name and version.

        :param name_version_str: accepts 'package_name==package_version' or 'package_name' format. The former is the
        format of the output of 'pip freeze'. The latter is name only.

        :return: name, version
        """
        # This is the standard format of 'pip freeze'
        if '==' in name_version_str:
            segs = name_version_str.rstrip().split('==')
            return segs[0].lstrip(), packaging.version.parse(segs[1])
        # This is a format conda uses, pending implementation
        elif '@ file://' in name_version_str:
            return None, None
        # This is a string with only name, mostly used for making query to PyPI
        elif ' ' not in name_version_str:
            return name_version_str, None
        return None, None

    def gen_pypi_info(self) -> (bool, dict):
        """
        Check if this package exists on PyPI, if yes get additional information of the package from PyPI.

        :return: if the package is found on PyPI, the package info
        """
        api_url = f"https://pypi.org/pypi/{self.name}/json"
        response = requests.get(api_url)
        if response.status_code == 200:
            package_info = response.json()
            if 'info' in package_info:
                self.is_found_on_pypi = True
                self.pypi_info = {'latest_version': package_info['info']['version'],
                                  'description': package_info['info']['description']}
                return
        self.is_found_on_pypi, self.pypi_info =  False, None

    def __str__(self):
        return (f'{self.name if self.name is not None else "unknown"}'
                f'=={self.version if self.version is not None else "unknown"}')


class PythonLibrary:
    """
    A class representing a Python library with the library path and the library name. The constructor takes a local
    path to the library. This is used to represent local Python libraries that are not installed via pip.
    """
    def __init__(self, library_path):
        self.library_path = Path(library_path)
        if self.library_path.exists():
            self.name = self.library_path.name

    #TODO: look for local metadata file to get library info
    def get_library_info(self):
        raise NotImplementedError


class PythonPackageSet:
    """
    A class representing a set of Python packages, which is usually installed in Python environment. It can also be
    used to represent a set of Python packages for further installation, which is the reason why 2 arithmetic operators
    are implemented for easy calculation of the union and difference of two PythonPackageSets.
    """
    def __init__(self, packages_str):
        """
        Initialize a PythonPackageSet from a string of packages, which is usually the output of 'pip freeze'. Using a
        empty string will create an empty PythonPackageSet.

        :param packages_str: a string of packages, each package is in the format of 'package_name==package_version'.
        """
        # The package_dict is a dictionary of {package_name: PythonPackage} for easy access
        self.package_dict = self._gen_package_set_from_str(packages_str)

    def _gen_package_set_from_str(self, packages_str) -> dict:
        package_list = [PythonPackage(package_str) for package_str in packages_str.strip().split('\n')]
        return {package.name: package for package in package_list if package.name}  # Filter out invalid ones

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
                if package.version > added_package_set.package_dict[package.name].version:
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
                if package.version > other.package_dict[package_name].version:
                    subtracted_package_set.package_dict[package_name] = self.package_dict[package_name]
        return subtracted_package_set

    def get_install_str(self):
        install_str = ' '.join([f'{package.name}=={package.version}' for package in self.package_dict.values()])
        return install_str

    def __str__(self):
        return self.get_install_str()



def list_venv_packages(env_path):
    if sys.platform == "win32":
        activate_script = env_path / 'Scripts' / 'activate.bat'
        command = f'cmd.exe /c "{activate_script} && pip freeze"'
    else:
        activate_script = env_path / 'bin' / 'activate'
        command = f'source {activate_script} && pip freeze'
    return run_command(command, expected_success_data_format=PythonPackageSet)


def get_blender_python_packages(blender_path):
    command = f'"{blender_path}" -m pip freeze'
    return run_command(command, expected_success_data_format=PythonPackageSet)


def install_packages(env_path, packages: PythonPackageSet):
    if sys.platform == "win32":
        activate_script = env_path / 'Scripts' / 'activate.bat'
        command = f'cmd.exe /c "{activate_script} && pip install {packages.get_install_str()}"'
    else:
        activate_script = env_path / 'bin' / 'activate'
        command = f'source {activate_script} && pip install {packages.get_install_str()}'
    return run_command(command)


def match_blender_python_packages(env_path, blender_path):
    blender_packages = get_blender_python_packages(blender_path)
    venv_packages = list_venv_packages(env_path)
    missing_packages = blender_packages.data - venv_packages.data
    if missing_packages.package_collection:
        result = install_packages(env_path, missing_packages)
    else:
        result = Result(True, 'No missing packages', None)
    return result
