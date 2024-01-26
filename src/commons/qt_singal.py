from PyQt6.QtCore import Qt, QSize, QObject, pyqtSignal, QFile, QIODevice, QSettings, QRect


class Signal(QObject):

    main_window_gui_loaded = pyqtSignal()
    load_sub_repo = pyqtSignal(object)  # Load a sub repo into the component table widgets
    load_component_in_editor = pyqtSignal(object)  # Load a component into the editor

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)
        return cls._instance


SIGNAL = Signal()
