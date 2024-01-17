from PyQt6.QtCore import QFile, QIODevice, QSettings
from PyQt6.QtGui import QFontDatabase

from commons.common import blog
from config import Config


def load_custom_fonts():
    """Load all custom fonts from the font directory."""
    font_dir = Config.root_dir / Config.resources_paths['font_dir']
    assert font_dir.exists(), f"Font directory not found at {font_dir}"
    font_files = font_dir.glob("*.ttf")
    # Remove italics fonts for now
    font_files = [font_file for font_file in font_files if 'Italic' not in font_file.name]
    for font_file in font_files:
        font_id = QFontDatabase.addApplicationFont(str(font_file))
        if font_id == -1:
            blog(3, f"Failed to load font from {font_file}")


def apply_stylesheet(app):
    """Apply the global stylesheet to the application."""
    load_custom_fonts()  # Load custom fonts first
    file = QFile(str(Config.root_dir / Config.resources_paths['qss']))
    if file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
        style_sheet = bytes(file.readAll()).decode("utf-8")
        file.close()
        app.setStyleSheet(style_sheet)
    else:
        raise FileNotFoundError("Failed to open stylesheet file.")


def get_app_icon_path(size: int = 64):
    """Get the application icon of the given size."""
    icon_path = Config.root_dir / Config.resources_paths['icons'][str(size)]
    assert icon_path.exists(), f"Icon file not found at {icon_path}"
    return icon_path



class BSettings(QSettings):
    """A singleton subclass of QSettings that supports boolean values."""

    _instance = None
    _is_initialized = False

    def __new__(cls, *args, **kwargs):
        """Guard against instantiation."""
        if not cls._instance:
            cls._instance = super().__new__(cls, Config.app_name, Config.app_name)
        return cls._instance

    def __init__(self):
        """Initialize the singleton instance."""
        if not self._is_initialized:
            super().__init__(Config.app_name, Config.app_name)
            self._is_initialized = True

    def set_value(self, subdir, key, value):
        key = f"{subdir}/{key}"
        super().setValue(key, value)

    def get_value(self, subdir, key, default=None):
        key = f"{subdir}/{key}"
        return super().value(key, default)

