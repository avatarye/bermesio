from PyQt6.QtCore import Qt, QSize, QObject, pyqtSignal, QFile, QIODevice, QSettings, QRect


class Signal(QObject):

    main_window_gui_loaded = pyqtSignal()

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)
        return cls._instance


SIGNAL = Signal()
