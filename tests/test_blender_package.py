from packaging.version import Version

from test_common import *

from components.python_package import PythonPackage, PythonLibrary, PythonPackageSet


def test_python_pacakge_class():
    pkg = PythonPackage('numpy==1.21.2')
    assert pkg.name == 'numpy'
    assert pkg.version == Version('1.21.2')
    pkg.gen_pypi_info()
    assert pkg.is_found_on_pypi
    pkg = PythonPackage('archspec @ file:///croot/archspec_1697725767277/work')
    assert str(pkg) == 'unknown==unknown'
    pkg = PythonPackage('my_package')
    assert str(pkg) == 'my_package==unknown'

    assert is_dillable(pkg), 'PythonPackage should be picklable'


def test_python_library_class():
    lib = PythonLibrary(r'C:\TechDepot\Github\bermesio')
    assert lib.name == 'bermesio'

    assert is_dillable(lib), 'PythonLibrary should be picklable'


def test_python_package_set_class():
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
    union = b4_packages + p12_packages
    assert len(union.package_dict) == 13
    assert union.package_dict['numpy'].version == Version('1.26.2')
    difference = b4_packages - p12_packages
    assert len(difference.package_dict) == 0
    difference = p12_packages - b4_packages
    assert len(difference.package_dict) == 2
    assert difference.package_dict['numpy'].version == Version('1.26.2')

    assert is_dillable(p12_packages), 'PythonPackageSet should be picklable'
