from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMainWindow

from commons.qt_common import BSettings


class BaseWindow(QMainWindow):

    name = 'unnamed_base_window'

    minimal_size = (640, 480)
    maximal_size = (1024, 768)

    def __init__(self):
        super().__init__()

        self._position = self.pos()
        self._is_mouse_holding = False

        self._setup_gui()
        self._setup_action()
        self._setup_window()

    def _setup_gui(self):
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName('BaseWindowCentralWidget')
        self.setCentralWidget(self.central_widget)

        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(2, 2, 2, 2)

    def _setup_action(self):
        ...

    def _setup_window(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.setMinimumSize(QSize(*self.minimal_size))
        self.setMaximumSize(QSize(*self.maximal_size))

        self.settings = BSettings()
        val = self.settings.get_value(self.name, 'geometry')
        if val:
            self.restoreGeometry(val)
        else:
            self.resize(*self.minimal_size)

    def show(self):
        super().show()
        self.activateWindow()

    def moveEvent(self, a0):
        self.settings.set_value(self.name, 'geometry', self.saveGeometry())
        super().moveEvent(a0)

    def resizeEvent(self, a0):

        self.settings.set_value(self.name, 'geometry', self.saveGeometry())
        super().resizeEvent(a0)