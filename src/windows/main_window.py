from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QButtonGroup, QStackedWidget, QScrollArea, QFrame

from commons.color import BColors
from commons.qt_common import get_app_icon_path
from commons.qt_singal import SIGNAL
from components.repository import Repository
from config import Config
from widgets.component_button import ComponentButton
from widgets.component_editor import DefaultEditor, ProfileEditor, BlenderSetupEditor, BlenderVenvEditor
from widgets.component_window_widget import ComponentWindowWidget
from widgets.foot_bar import MainWindowFootBar
from widgets.splitter import Splitter
from widgets.title_bar import MainWindowTitleBar
from windows.base_window import BaseWindow


class MainWindow(BaseWindow):

    name = 'MainWindow'

    def __init__(self):
        self.repo = self._load_repo()  # Load the repository first for some GUI elements have dependency on it.
        super().__init__()

    def _setup_gui(self):
        super()._setup_gui()
        self.titleBar = MainWindowTitleBar(self)
        self.splitter = Splitter(Qt.Orientation.Vertical, self)
        self.splitter.setObjectName('MainWindowSplitter')
        self.foot_bar = MainWindowFootBar(self)

        # Upper portion of the splitter
        self.widget_splitter_upper = QWidget(self)
        self.widget_splitter_upper.setMinimumHeight(20)
        self.vlayout_splitter_upper = QVBoxLayout(self.widget_splitter_upper)
        self.vlayout_splitter_upper.setContentsMargins(4, 0, 4, 0)
        self.vlayout_splitter_upper.setSpacing(0)
        # Component buttons
        self.hlayout_component_buttons = QHBoxLayout()
        self.hlayout_component_buttons.setContentsMargins(0, 0, 0, 0)
        self.hlayout_component_buttons.setSpacing(0)
        self.button_group_component_buttons = QButtonGroup(self)
        self.button_group_component_buttons.setObjectName('MainWindowButtonGroupComponentButtons')
        self.button_group_component_buttons.setExclusive(True)
        self.pushbutton_profile = ComponentButton(
            Config.get_component_settings('Profile'), parent=self)
        self.pushbutton_profile.setCheckable(True)
        self.pushbutton_blender_setup = ComponentButton(
            Config.get_component_settings('BlenderSetup'), parent=self)
        self.pushbutton_blender_setup.setCheckable(True)
        self.pushbutton_blender_program = ComponentButton(
            Config.get_component_settings('BlenderProgram'), parent=self)
        self.pushbutton_blender_program.setCheckable(True)
        self.pushbutton_blender_released_addon = ComponentButton(
            Config.get_component_settings('BlenderReleasedAddon'), parent=self)
        self.pushbutton_blender_released_addon.setCheckable(True)
        self.pushbutton_blender_released_script = ComponentButton(
            Config.get_component_settings('BlenderReleasedScript'), parent=self)
        self.pushbutton_blender_released_script.setCheckable(True)
        self.pushbutton_blender_venv = ComponentButton(
            Config.get_component_settings('BlenderVenv'), parent=self)
        self.pushbutton_blender_venv.setCheckable(True)
        self.pushbutton_blender_dev_addon = ComponentButton(
            Config.get_component_settings('BlenderDevAddon'), parent=self)
        self.pushbutton_blender_dev_addon.setCheckable(True)
        self.pushbutton_blender_dev_script = ComponentButton(
            Config.get_component_settings('BlenderDevScript'), parent=self)
        self.pushbutton_blender_dev_script.setCheckable(True)
        self.pushbutton_python_dev_library = ComponentButton(
            Config.get_component_settings('PythonDevLibrary'), parent=self)
        self.pushbutton_python_dev_library.setCheckable(True)
        self.button_group_component_buttons.addButton(self.pushbutton_profile)
        self.button_group_component_buttons.addButton(self.pushbutton_blender_setup)
        self.button_group_component_buttons.addButton(self.pushbutton_blender_program)
        self.button_group_component_buttons.addButton(self.pushbutton_blender_released_addon)
        self.button_group_component_buttons.addButton(self.pushbutton_blender_released_script)
        self.button_group_component_buttons.addButton(self.pushbutton_blender_venv)
        self.button_group_component_buttons.addButton(self.pushbutton_blender_dev_addon)
        self.button_group_component_buttons.addButton(self.pushbutton_blender_dev_script)
        self.button_group_component_buttons.addButton(self.pushbutton_python_dev_library)
        # Component widgets
        self.stacked_widget_components = QStackedWidget(self)
        self.stacked_widget_components.setObjectName('MainWindowStackedWidgetComponents')
        self.stacked_widget_components.setContentsMargins(0, 0, 0, 0)
        self.stacked_widget_components.setStyleSheet(f'border: 1px solid {BColors.sub_text.value}')
        self.component_widget_profile = ComponentWindowWidget(
            Config.get_component_settings('Profile'), self.repo.profile_repo, parent=self)
        self.component_widget_blender_setup = ComponentWindowWidget(
            Config.get_component_settings('BlenderSetup'), self.repo.blender_setup_repo, parent=self)
        self.component_widget_blender_program = ComponentWindowWidget(
            Config.get_component_settings('BlenderProgram'), self.repo.blender_program_repo, parent=self)
        self.component_widget_blender_released_addon = ComponentWindowWidget(
            Config.get_component_settings('BlenderReleasedAddon'), self.repo.blender_released_addon_repo, parent=self)
        self.component_widget_blender_released_script = ComponentWindowWidget(
            Config.get_component_settings('BlenderReleasedScript'), self.repo.blender_released_script_repo, parent=self)
        self.component_widget_blender_venv = ComponentWindowWidget(
            Config.get_component_settings('BlenderVenv'), self.repo.blender_venv_repo, parent=self)
        self.component_widget_blender_dev_addon = ComponentWindowWidget(
            Config.get_component_settings('BlenderDevAddon'), self.repo.blender_dev_addon_repo, parent=self)
        self.component_widget_blender_dev_script = ComponentWindowWidget(
            Config.get_component_settings('BlenderDevScript'), self.repo.blender_dev_script_repo, parent=self)
        self.component_widget_python_dev_library = ComponentWindowWidget(
            Config.get_component_settings('PythonDevLibrary'), self.repo.python_dev_library_repo, parent=self)
        # Lower portion of the splitter
        self.widget_splitter_lower = QScrollArea(self)
        self.widget_splitter_lower.setWidgetResizable(True)
        self.widget_splitter_lower.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.widget_splitter_lower.setMinimumHeight(40)
        self.widget_splitter_lower.setContentsMargins(0, 0, 0, 0)
        self.widget_splitter_lower.setFrameStyle(QFrame.Shape.NoFrame)
        self.widget_splitter_lower_widget = QWidget(self)
        self.vlayout_splitter_lower = QVBoxLayout(self.widget_splitter_lower_widget)
        self.vlayout_splitter_lower.setContentsMargins(4, 0, 4, 0)
        self.vlayout_splitter_lower.setSpacing(0)
        self.stacked_widget_editors = QStackedWidget(self)
        self.stacked_widget_editors.setObjectName('MainWindowStackedWidgetEditors')
        self.stacked_widget_editors.setContentsMargins(0, 0, 0, 0)
        self.stacked_widget_editors.setStyleSheet(f'border: 1px solid {BColors.sub_text.value}; '
                                                  f'background: transparent;')

        # Layout
        self.central_layout.addWidget(self.titleBar)
        self.central_layout.addWidget(self.splitter)
        self.splitter.addWidget(self.widget_splitter_upper)
        self.widget_splitter_upper.setLayout(self.vlayout_splitter_upper)
        self.vlayout_splitter_upper.addLayout(self.hlayout_component_buttons)
        self.hlayout_component_buttons.addWidget(self.pushbutton_profile)
        self.hlayout_component_buttons.addWidget(self.pushbutton_blender_setup)
        self.hlayout_component_buttons.addWidget(self.pushbutton_blender_program)
        self.hlayout_component_buttons.addWidget(self.pushbutton_blender_released_addon)
        self.hlayout_component_buttons.addWidget(self.pushbutton_blender_released_script)
        self.hlayout_component_buttons.addWidget(self.pushbutton_blender_venv)
        self.hlayout_component_buttons.addWidget(self.pushbutton_blender_dev_addon)
        self.hlayout_component_buttons.addWidget(self.pushbutton_blender_dev_script)
        self.hlayout_component_buttons.addWidget(self.pushbutton_python_dev_library)
        self.hlayout_component_buttons.addStretch()
        self.vlayout_splitter_upper.addWidget(self.stacked_widget_components)
        self.stacked_widget_components.addWidget(self.component_widget_profile)
        self.stacked_widget_components.addWidget(self.component_widget_blender_setup)
        self.stacked_widget_components.addWidget(self.component_widget_blender_program)
        self.stacked_widget_components.addWidget(self.component_widget_blender_released_addon)
        self.stacked_widget_components.addWidget(self.component_widget_blender_released_script)
        self.stacked_widget_components.addWidget(self.component_widget_blender_venv)
        self.stacked_widget_components.addWidget(self.component_widget_blender_dev_addon)
        self.stacked_widget_components.addWidget(self.component_widget_blender_dev_script)
        self.stacked_widget_components.addWidget(self.component_widget_python_dev_library)

        self.splitter.addWidget(self.widget_splitter_lower)
        self.widget_splitter_lower.setWidget(self.widget_splitter_lower_widget)
        self.widget_splitter_lower_widget.setLayout(self.vlayout_splitter_lower)
        self.vlayout_splitter_lower.addWidget(self.stacked_widget_editors)
        self.stacked_widget_editors.addWidget(DefaultEditor(self))
        self.stacked_widget_editors.addWidget(ProfileEditor(self))
        self.stacked_widget_editors.addWidget(BlenderSetupEditor(self))
        self.stacked_widget_editors.addWidget(BlenderVenvEditor(self))
        self.central_layout.addWidget(self.foot_bar)

        # Floating icon
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
        for widget in [self.splitter, self.button_group_component_buttons, self.stacked_widget_components,
                       self.stacked_widget_editors]:
            self._register_stateful_widget(widget)

    def _setup_action(self):
        super()._setup_action()

        self.pushbutton_profile.clicked.connect(lambda: self.stacked_widget_components.setCurrentWidget(
            self.component_widget_profile))
        self.pushbutton_blender_setup.clicked.connect(lambda: self.stacked_widget_components.setCurrentWidget(
            self.component_widget_blender_setup))
        self.pushbutton_blender_program.clicked.connect(lambda: self.stacked_widget_components.setCurrentWidget(
            self.component_widget_blender_program))
        self.pushbutton_blender_released_addon.clicked.connect(lambda: self.stacked_widget_components.setCurrentWidget(
            self.component_widget_blender_released_addon))
        self.pushbutton_blender_released_script.clicked.connect(lambda: self.stacked_widget_components.setCurrentWidget(
            self.component_widget_blender_released_script))
        self.pushbutton_blender_venv.clicked.connect(lambda: self.stacked_widget_components.setCurrentWidget(
            self.component_widget_blender_venv))
        self.pushbutton_blender_dev_addon.clicked.connect(lambda: self.stacked_widget_components.setCurrentWidget(
            self.component_widget_blender_dev_addon))
        self.pushbutton_blender_dev_script.clicked.connect(lambda: self.stacked_widget_components.setCurrentWidget(
            self.component_widget_blender_dev_script))
        self.pushbutton_python_dev_library.clicked.connect(lambda: self.stacked_widget_components.setCurrentWidget(
            self.component_widget_python_dev_library))

    def _setup_window(self):

        def get_total_component_button_width():
            total_width = 0
            for button in self.button_group_component_buttons.buttons():
                total_width += button.width()
            return total_width

        super()._setup_window()
        self.setWindowTitle(f'{Config.app_name} - {Config.app_subtitle}')
        self.setWindowIcon(QIcon(str(get_app_icon_path(64))))

        # Set the minimum width of the main window to the total width of the component buttons plus 8 pixels of padding.
        self.setMinimumWidth(get_total_component_button_width() + 16)

        # Set the component editor to the default editor.
        self.stacked_widget_editors.setCurrentIndex(0)

        # Emit the signal that the main window GUI is loaded for some widgets that need to adjust their GUI based on the
        # main window's GUI.
        SIGNAL.main_window_gui_loaded.emit()

    def _load_repo(self, repo_dir: str or Path = None):
        if repo_dir is None:
            repo_dir = Config.default_repo_dir
        repo_dir = r'c:\TechDepot\Github\bermesio\_test_data\win32\repos\example_repo'  # Test path
        result = Repository(repo_dir).create_instance()
        assert result, 'Error loading repo'
        repo = result.data
        repo.init_sub_repos()
        return repo

    def reload_repo(self, new_repo_dir: str or Path):
        # Clear the singleton instance of the repository and reload it.
        Repository.clear_singleton_instance()
        self.repo = self._load_repo(new_repo_dir)
        # Emits signals to notify the table widgets to reload their sub_repo data.
        for sub_repo in self.repo.sub_repos.values():
            SIGNAL.load_sub_repo.emit(sub_repo)
