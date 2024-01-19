from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QButtonGroup

from commons.colors import BColors
from commons.qt_common import get_app_icon_path
from config import Config
from widgets.component_button import ComponentButton
from widgets.foot_bar import MainWindowFootBar
from widgets.splitter import Splitter
from widgets.title_bar import MainWindowTitleBar
from windows.base_window import BaseWindow


class MainWindow(BaseWindow):

    name = 'main_window'

    def __init__(self):
        super().__init__()

    def _setup_gui(self):
        super()._setup_gui()
        self.titleBar = MainWindowTitleBar(self)
        self.splitter = Splitter(Qt.Orientation.Vertical, self)
        self.splitter.setObjectName('MainWindowSplitter')
        self.widget_splitter_upper = QWidget(self)
        self.vlayout_splitter_upper = QVBoxLayout(self.widget_splitter_upper)
        self.vlayout_splitter_upper.setContentsMargins(0, 0, 0, 0)
        # Component buttons
        self.hlayout_component_buttons = QHBoxLayout()
        self.hlayout_component_buttons.setContentsMargins(0, 0, 0, 0)
        self.hlayout_component_buttons.setSpacing(0)
        self.button_group_component_buttons = QButtonGroup(self)
        self.button_group_component_buttons.setExclusive(True)
        self.pushbutton_profiles = ComponentButton('PROFILES', '\U000f0004', BColors.profile.value, parent=self)
        self.pushbutton_profiles.setCheckable(True)
        self.pushbutton_setups = ComponentButton('SETUPS', '\U000f01d6', BColors.blender_setup.value, parent=self)
        self.pushbutton_setups.setCheckable(True)
        self.pushbutton_programs = ComponentButton('BLENDERS', '\U000f00ab', BColors.blender_program.value, parent=self)
        self.pushbutton_programs.setCheckable(True)
        self.pushbutton_addons = ComponentButton('ADDONS', '\U000f003c', BColors.blender_released_addon.value,
                                                 parent=self)
        self.pushbutton_addons.setCheckable(True)
        self.pushbutton_scripts = ComponentButton('SCRIPTS', '\U000f09ee', BColors.blender_released_script.value,
                                                  parent=self)
        self.pushbutton_scripts.setCheckable(True)
        self.pushbutton_venvs = ComponentButton('VENV', '\U000f0862', BColors.blender_venv.value, parent=self)
        self.pushbutton_venvs.setCheckable(True)
        self.pushbutton_dev_addons = ComponentButton('DEV ADDONS', '\U000f1754', BColors.blender_dev_addon.value,
                                                     parent=self)
        self.pushbutton_dev_addons.setCheckable(True)
        self.pushbutton_dev_scripts = ComponentButton('DEV SCRIPTS', '\U000f0dc9', BColors.blender_dev_script.value,
                                                      parent=self)
        self.pushbutton_dev_scripts.setCheckable(True)
        self.pushbutton_python_local_libs = ComponentButton('PYTHON LIBS', '\U0000e606',
                                                            BColors.python_local_library.value, parent=self)
        self.pushbutton_python_local_libs.setCheckable(True)
        self.button_group_component_buttons.addButton(self.pushbutton_profiles)
        self.button_group_component_buttons.addButton(self.pushbutton_setups)
        self.button_group_component_buttons.addButton(self.pushbutton_programs)
        self.button_group_component_buttons.addButton(self.pushbutton_addons)
        self.button_group_component_buttons.addButton(self.pushbutton_scripts)
        self.button_group_component_buttons.addButton(self.pushbutton_venvs)
        self.button_group_component_buttons.addButton(self.pushbutton_dev_addons)
        self.button_group_component_buttons.addButton(self.pushbutton_dev_scripts)
        self.button_group_component_buttons.addButton(self.pushbutton_python_local_libs)

        self.widget_splitter_lower = QWidget(self)
        self.vlayout_splitter_lower = QVBoxLayout(self.widget_splitter_lower)
        self.foot_bar = MainWindowFootBar(self)

        self.central_layout.addWidget(self.titleBar)
        self.central_layout.addWidget(self.splitter)
        self.splitter.addWidget(self.widget_splitter_upper)
        self.widget_splitter_upper.setLayout(self.vlayout_splitter_upper)
        self.vlayout_splitter_upper.addLayout(self.hlayout_component_buttons)
        self.hlayout_component_buttons.addWidget(self.pushbutton_profiles)
        self.hlayout_component_buttons.addWidget(self.pushbutton_setups)
        self.hlayout_component_buttons.addWidget(self.pushbutton_programs)
        self.hlayout_component_buttons.addWidget(self.pushbutton_addons)
        self.hlayout_component_buttons.addWidget(self.pushbutton_scripts)
        self.hlayout_component_buttons.addWidget(self.pushbutton_venvs)
        self.hlayout_component_buttons.addWidget(self.pushbutton_dev_addons)
        self.hlayout_component_buttons.addWidget(self.pushbutton_dev_scripts)
        self.hlayout_component_buttons.addWidget(self.pushbutton_python_local_libs)
        self.hlayout_component_buttons.addStretch()
        self.vlayout_splitter_upper.addStretch()
        self.splitter.addWidget(self.widget_splitter_lower)
        self.widget_splitter_lower.setLayout(self.vlayout_splitter_lower)
        self.vlayout_splitter_lower.addWidget(QLabel('Lower Widget'))

        # self.central_layout.addStretch()
        self.central_layout.addWidget(self.foot_bar)


        # floating_icon = QLabel(self)
        # floating_icon.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # floating_icon.setStyleSheet("background: transparent;")
        # floating_icon.setPixmap(QPixmap(str(get_app_icon_path(64))))
        # floating_icon.setFixedSize(64, 64)
        # floating_icon.move(4, 4)
        # floating_icon.show()
        # floating_icon.raise_()

        # Stateful widget registration needs to be done after the widget is created, or it will conflict with the
        # state saving functions.
        self._register_stateful_widget(self.splitter)

    def _setup_action(self):
        super()._setup_action()

    def _setup_window(self):
        super()._setup_window()
        self.setWindowTitle(f'{Config.app_name} - {Config.app_subtitle}')
        self.setWindowIcon(QIcon(str(get_app_icon_path(64))))
