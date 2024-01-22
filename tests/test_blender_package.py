from packaging.version import Version
from pathlib import Path

from testing_common import TESTDATA, is_dillable

from components.python_package import PythonLocalPackage, PythonPyPIPackage, PythonPackageSet


def test_python_local_package_class():
    bpy_package_path = Path(TESTDATA['blender_venv|0|bpy_package_path'])
    bpy_package = PythonLocalPackage(bpy_package_path)
    assert all([bpy_package.name == 'bpy', bpy_package.version == Version(TESTDATA['blender_venv|0|bpy_package_version'])]), \
        'PythonLocalPackage should be able to get the package name and version from its path'
    assert bpy_package.get_installation_str() == 'bpy==4.0.0', \
        'PythonLocalPackage should be able to get the installation string'
    assert is_dillable(bpy_package), 'PythonLocalPackage should be picklable'


def test_python_pypi_pacakge_class():
    pkg = PythonPyPIPackage('numpy==1.21.2')
    assert pkg.name == 'numpy', 'PythonPyPIPackage should be able to get the package name from its installation string'
    assert pkg.version == Version('1.21.2')
    pkg.gen_pypi_info(), 'PythonPyPIPackage should be able to get the package info from PyPI'
    assert pkg.is_found_on_pypi, 'PythonPyPIPackage should be able to get the package info from PyPI'
    pkg = PythonPyPIPackage('archspec @ file:///croot/archspec_1697725767277/work')
    assert str(pkg) == 'unknown==unknown', 'PythonPyPIPackage should be able to handle unknown package name and version'
    pkg = PythonPyPIPackage('my_package')
    assert str(pkg) == 'my_package==unknown', 'PythonPyPIPackage should be able to handle unknown package version'
    assert is_dillable(pkg), 'PythonPackage should be picklable'


def test_python_package_set_class():
    # Test PythonPackageSet with local package path
    venv_packagee_path = Path(TESTDATA['blender_venv|0|site_packages_path'])
    venv_packages = PythonPackageSet(venv_packagee_path)
    assert len(venv_packages.package_dict.values()) == 13

    # Test PythonPackageSet with installation string
    b4_packages_str = """
        autopep8==1.6.0
        certifi==2021.10.8
        charset-normalizer==2.0.10
        Cython==0.29.30
        idna==3.3
        meson==0.63.0
        numpy==1.23.5
        pycodestyle==2.8.0
        requests==2.27.1
        toml==0.10.2
        urllib3==1.26.8
        zstandard==0.16.0 
    """
    b4_packages = PythonPackageSet(b4_packages_str)
    assert len(b4_packages.package_dict.values()) == 12
    p12_packages_str = """
        autopep8==1.6.0
        certifi==2021.10.8
        charset-normalizer==2.0.10
        Cython==0.29.30
        idna==3.3
        meson==0.63.0
        numpy==1.26.2
        pycodestyle==2.8.0
        requests==2.27.1
        shapely==2.0.2
        toml==0.10.2
        urllib3==1.26.8
        zstandard==0.16.0
    """
    p12_packages = PythonPackageSet(p12_packages_str)
    assert len(p12_packages.package_dict) == 13

    # Test arithmetic operations
    union = b4_packages + p12_packages
    assert len(union.package_dict) == 13
    assert union.package_dict['numpy'].label_type == Version('1.26.2')
    difference = b4_packages - p12_packages
    assert len(difference.package_dict) == 0
    difference = p12_packages - b4_packages
    assert len(difference.package_dict) == 2
    assert difference.package_dict['numpy'].label_type == Version('1.26.2')

    # Test empty PythonPackageSet with add and remove operations
    empty = PythonPackageSet('')
    empty.add_package(PythonPyPIPackage('numpy==1.26.2'))
    local_bpy_package_path = Path(TESTDATA['blender_venv|0|bpy_package_path'])
    bpy_package = PythonLocalPackage(local_bpy_package_path)
    empty.add_package(bpy_package)
    assert len(empty.package_dict) == 2, 'PythonPackageSet should be able to add packages'
    empty.remove_package('numpy')
    assert len(empty.package_dict) == 1, 'PythonPackageSet should be able to remove packages using package name'
    empty.remove_package('non-exist-package')
    assert len(empty.package_dict) == 1, 'PythonPackageSet should not remove non-exist packages'
    empty.remove_package(bpy_package)
    assert len(empty.package_dict) == 0

    # Test dill-ability
    assert is_dillable(p12_packages), 'PythonPackageSet should be picklable'
