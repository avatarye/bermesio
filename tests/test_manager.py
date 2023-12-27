from pathlib import Path

from components.manager import ObjectPool
from components.blender_program import BlenderProgram


def test_object_pool_class():
    # Test pooling
    test_dill_file_path = Path(__file__).parent / 'test_object_pool.dill'
    ObjectPool.save_file_path = test_dill_file_path
    bp_unpooled = BlenderProgram(r'c:\TechDepot\AvatarTools\Blender\Launcher\stable\blender-4.0.1-windows-x64\blender.exe')
    assert ObjectPool.pool == {}, 'Not setting store_in_pool=True shouldn\'t pool the object.'
    bp0 = BlenderProgram(r'c:\TechDepot\AvatarTools\Blender\Launcher\stable\blender-4.0.1-windows-x64\blender.exe', store_in_pool=True)
    bp1 = BlenderProgram(r'c:\TechDepot\AvatarTools\Blender\Launcher\stable\blender-4.0.1-windows-x64\blender.exe', store_in_pool=True)
    assert bp0 is bp1, 'BlenderProgram objects initiated from the same path are not the same pooled object.'
    ObjectPool.remove(bp0)
    assert ObjectPool.pool == {}, 'ObjectPool.remove() did not remove the object from the pool.'

    # Test save and load
    bp0 = BlenderProgram(r'c:\TechDepot\AvatarTools\Blender\Launcher\stable\blender-4.0.1-windows-x64\blender.exe', store_in_pool=True)
    ObjectPool.save()
    ObjectPool.clear()
    ObjectPool.load()
    assert len(ObjectPool.pool) == 1, 'ObjectPool pickling is not working.'

    # Clear the test dill file
    ObjectPool.clear_save_file()
    assert not test_dill_file_path.exists(), 'ObjectPool.clear_save_file() is not working.'
