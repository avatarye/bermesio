from components.blender_addon import BlenderDirectoryAddon


class BlenderDevAddon(BlenderDirectoryAddon):
    """
    A class representing a Blender addon in development, which is a directory located in a non-repo path, typically the
    developer's own directory. The only format supported is a directory containing a __init__.py file in it, hence this
    class inherits from BlenderDirectoryAddon.
    """

    def __init__(self, addon_path):
        super().__init__(addon_path, repo_dir=False, delete_existing=False)
