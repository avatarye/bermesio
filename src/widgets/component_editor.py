from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPixmap, QColor, QPen, QIcon
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QFrame, QSpacerItem, QGridLayout,
                             QCheckBox, QPushButton)

from commons.color import BColors
from commons.qt_common import get_app_icon_path, LabelVerticalBar, get_glyph_icon
from commons.qt_singal import SIGNAL
from components.profile import BlenderLaunchConfig, VenvLaunchConfig
from components.repository import Repository
from config import Config
from widgets.button import ComponentOpsButton
from widgets.component_item import (ProfileItemWidget, BlenderProgramItemWidget, BlenderSetupItemWidget,
                                    BlenderVenvItemWidget, ComponentItemWidgetManager)
from widgets.component_table import ComponentTableWidget


class ComponentEditorDropWidget(QWidget):
    """
    A class that is used to visually represent a component contained within a component editor, such a BlenderProgram
    within a Profile editor. It accepts drag and drop which is the main way to link a component to tue component being
    edited. It also displays the linked component if there is any.
    """

    _component = None
    @property
    def component(self):
        return self._component

    @component.setter
    def component(self, value):
        self._component = value
        if hasattr(self, 'vlayout'):
            self.layout().removeWidget(self.component_widget)
            self.component_widget = ComponentItemWidgetManager.create(value, None) if value is not None else \
                self._get_empty_component_label()
            self.layout().addWidget(self.component_widget)

    def __init__(self, parent_editor, component_class_name):
        super().__init__(parent_editor)
        self.parent_editor = parent_editor
        self.component_class_name = component_class_name
        self.component_display_type = Config.component_settings[self.component_class_name]['display_text']
        self.component_color = Config.component_settings[self.component_class_name]['color']
        self.component = None
        self.setAcceptDrops(True)
        self.setFixedHeight(120)

        self._setup_gui()

    def _setup_gui(self):
        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.component_widget = self._get_empty_component_label()
        self.setLayout(self.vlayout)
        self.vlayout.addWidget(self.component_widget)

    def _get_empty_component_label(self):
        label_empty_component = QLabel(f'Drop a {self.component_display_type} here', parent=self)
        label_empty_component.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_empty_component.setStyleSheet(f'border: 0px; background: transparent; color: {BColors.text.value};'
                                                 f'font-family: {Config.font_settings["input_font"]}; font-size: 13px;'
                                                 f'font-weight: normal')
        return label_empty_component

    def _get_component_from_mime_data(self, mime_data):
        # Get the component uuid from the mime data, then retrieve the component from the Config.drag_drop_objects dict
        component = None
        if mime_data.hasFormat(Config.mime_custom_type_str):
            uuid = mime_data.data(Config.mime_custom_type_str).data().decode()
            if uuid in Config.drag_drop_objects:
                component = Config.drag_drop_objects[uuid]
        return component

    def dragEnterEvent(self, event):
        component = self._get_component_from_mime_data(event.mimeData())
        if component is not None and component.__class__.__name__ == self.component_class_name:
            self.component = component
            event.acceptProposedAction()

    def dropEvent(self, event):
        component = self._get_component_from_mime_data(event.mimeData())
        if component is not None and component.__class__.__name__ == self.component_class_name:
            self.component = component
            del Config.drag_drop_objects[component.uuid]
            event.acceptProposedAction()

    def paintEvent(self, event):
        # super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(0.05)
        painter.fillRect(self.rect(), QColor(self.component_color))
        if self.component is None:  # Draw dotted line when there is no component
            painter.setOpacity(0.2)
            border_pen = QPen(QColor(BColors.sub_text.value))
            border_pen.setWidth(2)
            border_pen.setStyle(Qt.PenStyle.DotLine)
        else:  # Draw solid line when there is a component
            painter.setOpacity(0.5)
            border_pen = QPen(QColor(self.component_color))
            border_pen.setWidth(2)
            border_pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(border_pen)
        painter.drawRect(QRect(1, 1, self.rect().width() - 2, self.rect().height() - 2))
        painter.end()


class ComponentEditor(QWidget):

    def __init__(self, component_class_name, parent_window=None):
        super().__init__()
        self.component_class_name = component_class_name
        self.component = None
        self.parent_window = parent_window
        self.component_setting_dict = Config.component_settings[self.component_class_name]
        self.name = self.component_setting_dict['name']
        self.setObjectName(f'MainWindowComponentEditor{self.name.title()}')
        self.color = self.component_setting_dict['color']

        self.sub_text_style = (f'font-family: {Config.font_settings["note_font"]}; font-size: 12px;'
                               f'font-weight: normal; border: 0px; background: transparent;')
        self.small_text_style = (f'font-family: {Config.font_settings["note_font"]}; font-size: 10px;'
                               f'font-weight: bold; border: 0px; background: transparent;')
        self.name_text_style = (f'font-family: {Config.font_settings["title_font"]}; font-size: 22px; '
                                f'color: {self.color}; font-weight: bold; border: 0px; background: transparent;')
        self.sub_name_text_style = (f'font-family: {Config.font_settings["title_font"]}; font-size: 16px; '
                                    f'color: {BColors.sub_text.value}; font-weight: bold; border: 0px; '
                                    f'background: transparent;')
        self.launch_option_check_box_style = """
            QCheckBox {
                font-family: %s;
                font-size: 11px;
                font-weight: bold;
                color: %s;
            }
            QCheckBox::indicator {
                width: 6px;
                height: 6px;
                border: 2px solid %s;
                border-radius: 4px;
                background: transparent;
            }
            QCheckBox::indicator:checked {
                width: 6px;
                height: 6px;
                border-radius: 5px;
                background: %s;
            }
        """ % (Config.font_settings['note_font'], BColors.sub_text.value, BColors.sub_text.value, self.color)
        self.button_style = """
            QPushButton {
                font-family: %s;
                font-size: 13px;
                font-weight: bold;
                color: %s;
                background: transparent;
                border: 2px solid %s;
                border-radius: 4px;
            }
            QPushButton::hover {
                background: %s;
                color: %s;
                border: 2px solid %s;
            }
        """ % (Config.font_settings['glyph_icon_font'], self.color, self.color, self.color, BColors.text.value,
               BColors.text.value)
        self.sub_title_icon_style = (f'font-family: {Config.font_settings["glyph_icon_font"]}; font-size: 16px;'
                                     f'border: 0px; background: transparent; color: {BColors.sub_text.value};')

        self._setup_gui()
        self._setup_action()

    def _setup_gui(self):
        # Set up the widgets
        self.hlayout = QHBoxLayout(self)
        self.hlayout.setContentsMargins(4, 4, 4, 4)
        self.hlayout.setSpacing(0)
        self.label_vertical_bar = LabelVerticalBar(self.color, 4, parent=self)
        self.label_vertical_bar.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.hlayout.addWidget(self.label_vertical_bar)

    def _setup_action(self):
        SIGNAL.load_component_in_editor.connect(self.load_component)

    def load_component(self, component):
        ...

    def _update_verification_label(self, label):
        if self.component is not None and self.component.verify():
            verification_pixmap = QIcon(get_glyph_icon('\U0000f058', Config.font_settings['glyph_icon_font'],
                                                       'green', 16)).pixmap(16, 16)
        else:
            verification_pixmap = QIcon(get_glyph_icon('\U0000f057', Config.font_settings['glyph_icon_font'],
                                                       'red', 16)).pixmap(16, 16)
        label.setPixmap(verification_pixmap)

    def paintEvent(self, event):
        # Draw the logo as background using the central widget as the reference
        central_widget = self.parent_window.findChild(QWidget, 'BaseWindowCentralWidget')
        pos_in_central_widget = self.mapTo(central_widget, self.pos())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(0.03)
        pixmap = QPixmap(str(get_app_icon_path(512))).scaled(384, 384, Qt.AspectRatioMode.KeepAspectRatio)
        painter.drawPixmap(int(central_widget.rect().width() / 2 - pixmap.width() / 2),
                           int(central_widget.rect().height() / 2 - pixmap.height() / 2)
                           - pos_in_central_widget.y() + 20, pixmap)
        painter.end()


class DefaultEditor(ComponentEditor):

    def __init__(self, parent_window):
        super().__init__('Default', parent_window)

    def _setup_gui(self):
        """
        Set up the GUIs for the default editor, which is different from the other component editors. So it doesn't
        call the super method.
        """
        self.hlayout = QHBoxLayout(self)
        self.hlayout.setContentsMargins(4, 4, 4, 4)
        self.hlayout.setSpacing(0)
        self.label_vertical_bar = LabelVerticalBar(self.color, 4, parent=self)
        self.label_vertical_bar.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_labels = QHBoxLayout(self)
        layout_labels.setContentsMargins(0, 0, 0, 0)
        layout_labels.setSpacing(8)
        layout_labels.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_click_icon = QLabel('\U000f0cfe', parent=self)
        self.label_click_icon.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; font-size: 40px;'
                                            f'border: 0px;' f'font-weight: normal; color: {BColors.sub_text.value};'
                                            f'background: transparent;')
        self.label_note = QLabel('Please double click on a Profile, Setup, or Venv item to edit.\n'
                                 'Tips: You can drag and drop a valid file or directory from the OS\n'
                                 'file manager into any of the tables above.', parent=self)
        self.label_note.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.label_note.setStyleSheet(self.sub_text_style)

        self.hlayout.addWidget(self.label_vertical_bar)
        self.hlayout.addLayout(layout_labels)
        layout_labels.addWidget(self.label_click_icon)
        layout_labels.addWidget(self.label_note)

    def load_component(self, component):
        if component is None:
            self.parent().setCurrentWidget(self)


class ProfileEditor(ComponentEditor):

    def __init__(self, parent_window=None):
        super().__init__('Profile', parent_window)


    def _setup_gui(self):
        super()._setup_gui()

        # Define widgets
        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(4, 0, 0, 0)
        vlayout.setSpacing(4)
        label_editor_type = QLabel('A Profile consists of three components: a Blender program, a Setup, and an '
                                   'optional Venv. You can launch Blender in the usual window mode or the Venv in the '
                                   'command line window. Additionally, you can adjust the launch options here.',
                                   parent=self)
        label_editor_type.setWordWrap(True)
        label_editor_type.setStyleSheet(self.small_text_style)
        spacer_label_editor_type = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        ## Define the name label
        hlayout_component_name = QHBoxLayout(self)
        self.label_component_verified = QLabel(self)
        self._update_verification_label(self.label_component_verified)
        self.label_component_name = QLabel('name', parent=self)
        self.label_component_name.setStyleSheet(self.name_text_style)
        self.button_rename = ComponentOpsButton('\U0000f45a', self.color, parent=self)
        self.button_rename.setToolTip('Rename')

        ## Define the drop widgets
        self.hlayout_components = QHBoxLayout(self)
        self.hlayout_components.setSpacing(4)
        self.drop_widget_blender_program = ComponentEditorDropWidget(self, 'BlenderProgram')
        self.drop_widget_blender_setup = ComponentEditorDropWidget(self, 'BlenderSetup')
        self.drop_widget_blender_venv = ComponentEditorDropWidget(self, 'BlenderVenv')
        spacer_label_drop_widgets = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        ## Define the launch options
        hlayout_launch_options = QHBoxLayout(self)
        hlayout_launch_options.setSpacing(12)
        vlayout_launch_blender = QVBoxLayout(self)
        vlayout_launch_blender.setSpacing(4)
        hlayout_launch_blender_title = QHBoxLayout(self)
        hlayout_launch_blender_title.setSpacing(4)
        hlayout_launch_blender_title.setContentsMargins(0, 0, 0, 0)
        label_launch_blender_icon = QLabel('\U000f00ab', parent=self)
        label_launch_blender_icon.setStyleSheet(self.sub_title_icon_style)
        label_launch_blender = QLabel('Blender Launch Options', parent=self)
        label_launch_blender.setStyleSheet(self.sub_name_text_style)
        frame_launch_blender = QFrame(self)
        frame_launch_blender.setFrameShape(QFrame.Shape.HLine)
        frame_launch_blender.setStyleSheet(f'color: {BColors.sub_text.value};')
        glayout_launch_blender = QGridLayout(self)
        glayout_launch_blender.setSpacing(4)
        glayout_launch_blender.setContentsMargins(0, 0, 0, 0)
        self.checkbox_launch_blender_user_config = QCheckBox('User config', parent=self)
        self.checkbox_launch_blender_user_config.setToolTip('Use the user config included in the Setup linked in this '
                                                       'profile.')
        self.checkbox_launch_blender_user_config.setStyleSheet(self.launch_option_check_box_style)
        self.checkbox_launch_blender_user_addons_scripts = QCheckBox('User addons/scripts', parent=self)
        self.checkbox_launch_blender_user_addons_scripts.setToolTip('Use addons and scripts included in the Setup linked in'
                                                               'this profile.')
        self.checkbox_launch_blender_user_addons_scripts.setStyleSheet(self.launch_option_check_box_style)
        self.checkbox_launch_blender_venv_site_packages = QCheckBox('Venv site-packages', parent=self)
        self.checkbox_launch_blender_venv_site_packages.setToolTip('Include the site-packages from the Venv linked in this '
                                                              'profile, if any.')
        self.checkbox_launch_blender_venv_site_packages.setStyleSheet(self.launch_option_check_box_style)
        self.checkbox_launch_blender_venv_bpy = QCheckBox('Venv bpy package', parent=self)
        self.checkbox_launch_blender_venv_bpy.setToolTip('Include the bpy package from the Venv linked in this profile, if '
                                                    'any.')
        self.checkbox_launch_blender_venv_bpy.setStyleSheet(self.launch_option_check_box_style)
        self.checkbox_launch_blender_venv_python_dev_libs = QCheckBox('Venv Python dev libraries', parent=self)
        self.checkbox_launch_blender_venv_python_dev_libs.setToolTip('Include the Python dev libraries from the Venv linked '
                                                                'in this profile, if any.')
        self.checkbox_launch_blender_venv_python_dev_libs.setStyleSheet(self.launch_option_check_box_style)
        spacer_launch_blender_options = QSpacerItem(10, 6, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        hlayout_blender_launch_button = QHBoxLayout(self)
        self.button_launch_blender = QPushButton('\U000f14df Launch Blender', parent=self)
        self.button_launch_blender.setFixedSize(144, 24)
        self.button_launch_blender.setStyleSheet(self.button_style)
        vlayout_launch_venv = QVBoxLayout(self)
        vlayout_launch_venv.setSpacing(4)
        hlayout_launch_venv_title = QHBoxLayout(self)
        hlayout_launch_venv_title.setSpacing(4)
        hlayout_launch_venv_title.setContentsMargins(0, 0, 0, 0)
        label_launch_venv_icon = QLabel('\U000f0862', parent=self)
        label_launch_venv_icon.setStyleSheet(self.sub_title_icon_style)
        label_launch_venv = QLabel('Virtual Environment Launch Options', parent=self)
        label_launch_venv.setStyleSheet(self.sub_name_text_style)
        frame_launch_venv = QFrame(self)
        frame_launch_venv.setFrameShape(QFrame.Shape.HLine)
        frame_launch_venv.setStyleSheet(f'color: {BColors.sub_text.value};')
        glayout_launch_venv = QGridLayout(self)
        self.checkbox_launch_venv_bpy = QCheckBox('Venv bpy package', parent=self)
        self.checkbox_launch_venv_bpy.setToolTip('Include the bpy package from the Venv linked in this profile, if any.')
        self.checkbox_launch_venv_bpy.setStyleSheet(self.launch_option_check_box_style)
        self.checkbox_launch_venv_python_dev_libs = QCheckBox('Venv Python dev libraries', parent=self)
        self.checkbox_launch_venv_python_dev_libs.setToolTip('Include the Python dev libraries from the Venv linked in this '
                                                        'profile, if any.')
        self.checkbox_launch_venv_python_dev_libs.setStyleSheet(self.launch_option_check_box_style)
        spacer_launch_venv_options = QSpacerItem(10, 6, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        hlayout_venv_launch_button = QHBoxLayout(self)
        self.button_launch_venv = QPushButton('\U000f14df Launch Venv', parent=self)
        self.button_launch_venv.setFixedSize(124, 24)
        self.button_launch_venv.setStyleSheet(self.button_style)

        # Define layout
        self.hlayout.addLayout(vlayout)
        vlayout.addWidget(label_editor_type)
        vlayout.addItem(spacer_label_editor_type)
        vlayout.addLayout(hlayout_component_name)
        hlayout_component_name.addWidget(self.label_component_verified)
        hlayout_component_name.addWidget(self.label_component_name)
        hlayout_component_name.addWidget(self.button_rename)
        hlayout_component_name.addStretch()
        vlayout.addLayout(self.hlayout_components)
        self.hlayout_components.addWidget(self.drop_widget_blender_program)
        self.hlayout_components.addWidget(self.drop_widget_blender_setup)
        self.hlayout_components.addWidget(self.drop_widget_blender_venv)
        vlayout.addItem(spacer_label_drop_widgets)
        vlayout.addLayout(hlayout_launch_options)
        hlayout_launch_options.addLayout(vlayout_launch_blender)
        vlayout_launch_blender.addLayout(hlayout_launch_blender_title)
        hlayout_launch_blender_title.addWidget(label_launch_blender_icon)
        hlayout_launch_blender_title.addWidget(label_launch_blender)
        hlayout_launch_blender_title.addStretch()
        vlayout_launch_blender.addWidget(frame_launch_blender)
        vlayout_launch_blender.addLayout(glayout_launch_blender)
        glayout_launch_blender.addWidget(self.checkbox_launch_blender_user_config, 0, 0, 1, 1)
        glayout_launch_blender.addWidget(self.checkbox_launch_blender_user_addons_scripts, 0, 1, 1, 1)
        glayout_launch_blender.addWidget(self.checkbox_launch_blender_venv_site_packages, 1, 0, 1, 1)
        glayout_launch_blender.addWidget(self.checkbox_launch_blender_venv_bpy, 1, 1, 1, 1)
        glayout_launch_blender.addWidget(self.checkbox_launch_blender_venv_python_dev_libs, 2, 0, 1, 1)
        vlayout_launch_blender.addItem(spacer_launch_blender_options)
        vlayout_launch_blender.addLayout(hlayout_blender_launch_button)
        hlayout_blender_launch_button.addStretch()
        hlayout_blender_launch_button.addWidget(self.button_launch_blender)
        hlayout_blender_launch_button.addStretch()
        vlayout_launch_blender.addStretch()
        hlayout_launch_options.addLayout(vlayout_launch_venv)
        vlayout_launch_venv.addLayout(hlayout_launch_venv_title)
        hlayout_launch_venv_title.addWidget(label_launch_venv_icon)
        hlayout_launch_venv_title.addWidget(label_launch_venv)
        hlayout_launch_venv_title.addStretch()
        vlayout_launch_venv.addWidget(frame_launch_venv)
        vlayout_launch_venv.addLayout(glayout_launch_venv)
        glayout_launch_venv.addWidget(self.checkbox_launch_venv_bpy, 0, 0, 1, 1)
        glayout_launch_venv.addWidget(self.checkbox_launch_venv_python_dev_libs, 0, 1, 1, 1)
        vlayout_launch_venv.addItem(spacer_launch_venv_options)
        vlayout_launch_venv.addLayout(hlayout_venv_launch_button)
        hlayout_venv_launch_button.addStretch()
        hlayout_venv_launch_button.addWidget(self.button_launch_venv)
        hlayout_venv_launch_button.addStretch()
        vlayout_launch_venv.addStretch()
        vlayout.addStretch()

    def _setup_action(self):
        super()._setup_action()
        self._launch_option_checkbox_event_action('connect')
        self.button_launch_blender.clicked.connect(self._launch_blender)
        self.button_launch_venv.clicked.connect(self._launch_venv)

    def _launch_option_checkbox_event_action(self, action):
        checkboxes = [self.checkbox_launch_blender_user_config, self.checkbox_launch_blender_user_addons_scripts,
                      self.checkbox_launch_blender_venv_site_packages, self.checkbox_launch_blender_venv_bpy,
                      self.checkbox_launch_blender_venv_python_dev_libs, self.checkbox_launch_venv_bpy,
                      self.checkbox_launch_venv_python_dev_libs]
        for checkbox in checkboxes:
            if action == 'connect':
                checkbox.stateChanged.connect(self.save_launch_configs_in_profile)
            elif action == 'disconnect':
                checkbox.stateChanged.disconnect(self.save_launch_configs_in_profile)
            else:
                raise ValueError(f'Invalid action: {action}')

    def save_launch_configs_in_profile(self):
        if self.component is not None:
            blender_launch_config = BlenderLaunchConfig()
            blender_launch_config.if_use_blender_setup_config = self.checkbox_launch_blender_user_config.isChecked()
            blender_launch_config.if_use_blender_setup_addons_scripts = (
                self.checkbox_launch_blender_user_addons_scripts.isChecked())
            blender_launch_config.if_include_venv_site_packages = (
                self.checkbox_launch_blender_venv_site_packages.isChecked())
            blender_launch_config.if_include_venv_bpy = self.checkbox_launch_blender_venv_bpy.isChecked()
            blender_launch_config.if_include_venv_python_dev_libs = (
                self.checkbox_launch_blender_venv_python_dev_libs.isChecked())
            self.component.update_launch_config(blender_launch_config)
            venv_launch_config = VenvLaunchConfig()
            venv_launch_config.if_include_venv_bpy = self.checkbox_launch_venv_bpy.isChecked()
            venv_launch_config.if_include_venv_python_dev_libs = self.checkbox_launch_venv_python_dev_libs.isChecked()
            self.component.update_launch_config(venv_launch_config)

    def _load_launch_configs(self):
        if self.component is not None:
            self._launch_option_checkbox_event_action('disconnect')
            blender_launch_config = self.component.blender_launch_config
            self.checkbox_launch_blender_user_config.setChecked(blender_launch_config.if_use_blender_setup_config)
            self.checkbox_launch_blender_user_addons_scripts.setChecked(
                blender_launch_config.if_use_blender_setup_addons_scripts)
            self.checkbox_launch_blender_venv_site_packages.setChecked(blender_launch_config.if_include_venv_site_packages)
            self.checkbox_launch_blender_venv_bpy.setChecked(blender_launch_config.if_include_venv_bpy)
            self.checkbox_launch_blender_venv_python_dev_libs.setChecked(
                blender_launch_config.if_include_venv_python_dev_libs)
            venv_launch_config = self.component.venv_launch_config
            self.checkbox_launch_venv_bpy.setChecked(venv_launch_config.if_include_venv_bpy)
            self.checkbox_launch_venv_python_dev_libs.setChecked(venv_launch_config.if_include_venv_python_dev_libs)
            self._launch_option_checkbox_event_action('connect')

    def _launch_blender(self):
        if self.component is not None:
            self.component.launch_blender(self.component.blender_launch_config)

    def _launch_venv(self):
        if self.component is not None:
            self.component.launch_venv(self.component.venv_launch_config)

    def verify_and_update_gui(self):
        self._update_verification_label(self.label_component_verified)
        self.button_launch_venv.setEnabled(self.component.blender_venv is not None
                                           and self.component.blender_venv.verify())
        self.button_launch_blender.setEnabled(self.component.blender_program is not None
                                              and self.component.blender_program.verify())

    def load_component(self, component):
        if component.__class__.__name__ == self.component_class_name:
            self.component = component
            self.label_component_name.setText(self.component.name)
            self.drop_widget_blender_program.component = component.blender_program
            self.drop_widget_blender_setup.component = component.blender_setup
            self.drop_widget_blender_venv.component = component.blender_venv
            self._load_launch_configs()
            self.verify_and_update_gui()
            self.parent().setCurrentWidget(self)


class BlenderSetupEditor(ComponentEditor):
    def __init__(self, parent_window=None):
        super().__init__('BlenderSetup', parent_window)

    def _setup_gui(self):
        super()._setup_gui()

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)
        label_editor_type = QLabel('Setup Editor', parent=self)
        label_editor_type.setStyleSheet(f'font-family: {Config.font_settings["label_font"]}; font-size: 12px; '
                                        f'font-weight: bold; border: 0px;'
                                        f'background: transparent, color: {self.color};')
        label_component_name = QLabel('name', parent=self)

        self.hlayout.addLayout(vlayout)
        vlayout.addWidget(label_editor_type)
        vlayout.addWidget(label_component_name)

    def load_component(self, component):
        if component.__class__.__name__ == self.component_class_name:
            self.parent().setCurrentWidget(self)


class BlenderVenvEditor(ComponentEditor):
    def __init__(self, parent_window=None):
        super().__init__('BlenderVenv', parent_window)

    def load_component(self, component):
        if component.__class__.__name__ == self.component_class_name:
            self.parent().setCurrentWidget(self)
