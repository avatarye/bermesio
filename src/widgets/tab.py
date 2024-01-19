from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QTabBar
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QIcon

from config import Config
from commons.colors import BColors
from commons.common import Result, ResultList, blog
from commons.qt_common import get_glyph_icon


class Tab(QWidget):

    def __init__(self, parent_window: QWidget):
        super().__init__()
        self.parent_window = parent_window
        self._setup_gui()
        self._setup_action()

    def _setup_gui(self):

        label_01_logo = QLabel('\U000f0004')
        label_01_logo.setStyleSheet('font-family: "JetBrainsMono NFP"; font-size: 16px; font-weight: bold; color: #F92674;')
        label_01 = QLabel('Profiles')
        label_01.setStyleSheet('font-family: "Open Sans SemiCondensed"; font-size: 14px; font-weight: bold; color: #F92672;')
        label_02_logo = QLabel('\U000f01d6')
        label_02_logo.setStyleSheet('font-family: "JetBrainsMono NFP"; font-size: 16px; font-weight: bold; color: #AE81FF;')
        label_02 = QLabel('Setups')
        label_02.setStyleSheet('font-family: "Open Sans SemiCondensed"; font-size: 14px; font-weight: bold; color: #AE81FF;')
        label_03_logo = QLabel('\U000f00ab')
        label_03_logo.setStyleSheet('font-family: "JetBrainsMono NFP"; font-size: 16px; font-weight: bold; color: #FD971F;')
        label_03 = QLabel('Blenders')
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

    def _setup_action(self):
        ...


class ProfileTab(Tab):

    name = 'Profiles'
    icon_name = '\U000f0004Profiles'
    color = BColors.profile.value

    def __init__(self, parent_window: QWidget):
        super().__init__(parent_window)
        self.icon = get_glyph_icon('\U000f0004', 'JetBrainsMono NFP', self.color, 16)

