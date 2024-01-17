from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor, QPixmap
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

from commons.qt_common import get_app_icon_path
from config import Config


class TitleBar(QWidget):

    def __init__(self, parent_window: QWidget):
        super().__init__()
        self.parent_window = parent_window
        self._setup_gui()
        self._setup_action()

    def _setup_gui(self):
        self.setContentsMargins(0, 0, 0, 0)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(2)
        self.setLayout(self.layout)

    def _setup_action(self):
        ...

    def mousePressEvent(self, event):
        self.parent_window._position = event.globalPosition().toPoint()
        self.parent_window._is_mouse_holding = True
        self.parent_window.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouseMoveEvent(self, event):
        if self.parent_window._is_mouse_holding:
            delta = QPoint(event.globalPosition().toPoint() - self.parent_window._position)
            self.parent_window.move(self.parent_window.x() + delta.x(), self.parent_window.y() + delta.y())
            self.parent_window._position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.parent_window._is_mouse_holding = False
        self.parent_window.setCursor(QCursor(Qt.CursorShape.ArrowCursor))


class MainWindowTitleBar(TitleBar):

    def __init__(self, parent_window: QWidget):
        super().__init__(parent_window)
        self.parent_window = parent_window

    def _setup_gui(self):
        super()._setup_gui()

        self.lable_logo = QLabel()
        self.lable_logo.setFixedSize(32, 32)
        self.lable_logo.setPixmap(QPixmap(str(get_app_icon_path(32))))
        self.lable_app_title = QLabel(f'{Config.app_name.upper()} - {Config.app_subtitle}')
        self.lable_app_title.setStyleSheet("""
            font-family: "JetBrainsMono NFP", sans-serif;
            color: #F8F8F2;
            font-size: 12pt;
            font-weight: normal;
        """)

        button_stylesheet = """
        QPushButton {
            font-family: "JetBrainsMono NFP", sans-serif;
            color: #75715E;
            font-size: 16pt;
            background-color: transparent;
            border: none;
        }
        QPushButton:hover { color: #F8F8F2; }
        QPushButton:pressed { color: #75715E; }
        """

        close_button_stylesheet = """
        QPushButton {
            font-family: "JetBrainsMono NFP", sans-serif;
            color: #75715E;
            font-size: 16pt;
            background-color: transparent;
            border: none;
        }
        QPushButton:hover { color: #F92672; }
        QPushButton:pressed { color: #75715E; }
        """

        self.pushbutton_document = QPushButton('\U0000f02d')
        self.pushbutton_document.setFixedSize(32, 32)
        self.pushbutton_document.setStyleSheet(button_stylesheet)
        self.pushbutton_preferences = QPushButton('\U0000f013')
        self.pushbutton_preferences.setFixedSize(32, 32)
        self.pushbutton_preferences.setStyleSheet(button_stylesheet)
        self.pushbutton_minimize = QPushButton('\U0000e224')
        self.pushbutton_minimize.setFixedSize(32, 32)
        self.pushbutton_minimize.setStyleSheet(button_stylesheet)
        self.pushbutton_close = QPushButton('\U0000f2d3')
        self.pushbutton_close.setFixedSize(32, 32)
        self.pushbutton_close.setStyleSheet(close_button_stylesheet)

        self.layout.addWidget(self.lable_logo)
        self.layout.addWidget(self.lable_app_title)
        self.layout.addStretch()
        self.layout.addWidget(self.pushbutton_document)
        self.layout.addWidget(self.pushbutton_preferences)
        self.layout.addWidget(self.pushbutton_minimize)
        self.layout.addWidget(self.pushbutton_close)

    def _setup_action(self):
        super()._setup_action()
        self.pushbutton_minimize.clicked.connect(self.parent_window.showMinimized)
        self.pushbutton_close.clicked.connect(self.parent_window.close)
