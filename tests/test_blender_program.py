from pathlib import Path

from packaging.version import Version

from components.blender_program import BlenderProgram


def test_blender_program_class():
    # This test will only succeed if Blender is installed at the given path.
    blender_exe_path = r'c:\TechDepot\AvatarTools\Blender\Launcher\stable\blender-4.0.1-windows-x64\blender.exe'
    blender_program = BlenderProgram(blender_exe_path)
    python_exe_path = Path(r'c:\TechDepot\AvatarTools\Blender\Launcher\stable\blender-4.0.1-windows-x64\4.0\python\bin\python.exe')
    assert blender_program.python_exe_path == python_exe_path
    assert blender_program.python_version == Version('3.10.13')
    assert blender_program.blender_version == Version('4.0.1')
    assert len(blender_program.python_packages.package_dict) == 12
