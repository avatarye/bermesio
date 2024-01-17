from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel

from config import Config


class LabelSizeGripper(QLabel):

    def __init__(self, parent_window: QWidget):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setText('\U000f045d')

    def mousePressEvent(self, event):
        self.parent_window._position = event.globalPosition().toPoint()
        self.parent_window._is_mouse_holding = True
        self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))

    def mouseMoveEvent(self, event):
        if self.parent_window._is_mouse_holding:
            current_position = event.globalPosition().toPoint()
            delta = current_position - self.parent_window._position
            self.parent_window.resize( self.parent_window.width() + delta.x(), self.parent_window.height() + delta.y())
            self.parent_window._position = current_position

    def mouseReleaseEvent(self, event):
        self.parent_window._is_mouse_holding = False
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))


class MainWindowFootBar(QWidget):

    def __init__(self, parent_window: QWidget):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setObjectName('MainWindowFootBar')
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(20)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(4, 0, 4, 0)
        self.label_version = QLabel(f'{Config.app_last_update} ({Config.app_version})')
        self.label_version.setStyleSheet('font-size: 10pt')
        self.lable_size_gripper = LabelSizeGripper(self.parent_window)
        self.lable_size_gripper.setStyleSheet("""
            QLabel {
                font-family: "JetBrainsMono NFP", sans-serif;
                font-size: 20pt;
                background-color: transparent;
            }
            QLabel:hover {color: #F8F8F2}
        """)

        self.setLayout(self.layout)
        self.layout.addWidget(self.label_version)
        self.layout.addStretch()
        self.layout.addWidget(self.lable_size_gripper)
