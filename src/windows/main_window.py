from PyQt6.QtCore import Qt, QPoint, QSize, QSettings
from PyQt6.QtGui import QIcon, QPixmap, QCursor
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QStatusBar, QPushButton


from commons.qt_common import get_app_icon_path, BSettings
from config import Config
from widgets.title_bar import MainWindowTitleBar
from widgets.foot_bar import MainWindowFootBar
from windows.base_window import BaseWindow


class MainWindow(BaseWindow):

    name = 'main_window'

    def __init__(self):
        super().__init__()

    def _setup_gui(self):
        super()._setup_gui()
        self.titleBar = MainWindowTitleBar(self)
        self.hbox = QHBoxLayout()
        label_01 = QLabel('\U0000f427Profiles')
        label_01.setStyleSheet('font-family: "Open Sans SemiCondensed"; font-size: 14px; font-weight: bold; color: #F92672;')
        label_02 = QLabel('\U0000f4b7Setups')
        label_02.setStyleSheet('font-family: "Open Sans SemiCondensed"; font-size: 14px; font-weight: bold; color: #AE81FF;')
        label_03 = QLabel('\U000f00abBlenders')
        label_03.setStyleSheet('font-family: "Open Sans SemiCondensed"; font-size: 14px; font-weight: bold; color: #FD971F;')
        label_04 = QLabel('\U0000f4d0Addons')
        label_04.setStyleSheet('font-family: "Open Sans SemiCondensed"; font-size: 14px; font-weight: bold; color: #E69F66;')
        label_05 = QLabel('\U000f0bc3Scripts')
        label_05.setStyleSheet('font-family: "Open Sans SemiCondensed"; font-size: 14px; font-weight: bold; color: #E6DB74;')
        label_06 = QLabel('\U000f1463Venvs')
        label_06.setStyleSheet('font-family: "Open Sans SemiCondensed"; font-size: 14px; font-weight: bold; color: #A6E22E;')
        label_07 = QLabel('\U000f1725Dev Addons')
        label_07.setStyleSheet('font-family: "Open Sans SemiCondensed"; font-size: 14px; font-weight: bold; color: #66D9EF;')
        label_08 = QLabel('\U000f1726Dev Scripts')
        label_08.setStyleSheet('font-family: "Open Sans SemiCondensed"; font-size: 14px; font-weight: bold; color: #268BD2;')
        label_09 = QLabel('\U0000e606Local Libs')
        label_09.setStyleSheet('font-family: "Open Sans SemiCondensed"; font-size: 14px; font-weight: bold; color: #265787;')
        self.foot_bar = MainWindowFootBar(self)

        self.central_layout.addWidget(self.titleBar)
        self.central_layout.addLayout(self.hbox)
        self.hbox.addWidget(label_01)
        self.hbox.addWidget(label_02)
        self.hbox.addWidget(label_03)

        self.hbox.addWidget(label_04)
        self.hbox.addWidget(label_05)
        self.hbox.addWidget(label_06)
        self.hbox.addWidget(label_07)
        self.hbox.addWidget(label_08)
        self.hbox.addWidget(label_09)
        self.hbox.addStretch()
        self.central_layout.addStretch()
        self.central_layout.addWidget(self.foot_bar)

        # floating_icon = QLabel(self)
        # floating_icon.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # floating_icon.setStyleSheet("background: transparent;")
        # floating_icon.setPixmap(QPixmap(str(get_app_icon_path(32))))
        # floating_icon.setFixedSize(32, 32)
        # floating_icon.move(4, 4)
        # floating_icon.show()
        # floating_icon.raise_()


    def _setup_action(self):
        super()._setup_action()

    def _setup_window(self):
        super()._setup_window()
        self.setWindowTitle(f'{Config.app_name} - {Config.app_subtitle}')
        self.setWindowIcon(QIcon(str(get_app_icon_path(64))))
