from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLineEdit

from commons.qt_common import get_app_icon_path, LabelVerticalBar
from components.repository import Repository
from config import Config
from widgets.button import ComponentOpsButton
from widgets.component_table import ComponentTableWidget


class ComponentWindowWidget(QWidget):
    """A base class for the widget that are used in the stacked widget of the main window."""

    def __init__(self, component_setting_dict, sub_repo, parent=None):
        super().__init__(parent)
        self.component_setting_dict = component_setting_dict
        self.name = component_setting_dict['name']
        self.setObjectName(f'MainWindowComponentWidget{self.name.title()}')
        self.color = component_setting_dict['color']
        self.sub_repo = sub_repo
        self.repo = Repository.get_singleton_instance()

        self._setup_gui()
        self._setup_action()

    def _setup_gui(self):
        # Set up the widgets
        self.hlayout = QHBoxLayout(self)
        self.hlayout.setContentsMargins(4, 4, 4, 4)
        self.hlayout.setSpacing(4)
        self.label_vertical_bar = LabelVerticalBar(self.color, 4, parent=self)
        self.label_vertical_bar.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.component_table = ComponentTableWidget(self.component_setting_dict, self.sub_repo, parent=self)
        self.vlayout_table_top_bar = QVBoxLayout(self)
        self.vlayout_table_top_bar.setContentsMargins(0, 0, 0, 0)
        self.vlayout_table_top_bar.setSpacing(2)
        self.hlayout_top_bar = QHBoxLayout(self)
        self.hlayout_top_bar.setSpacing(4)
        self.line_edit_search = QLineEdit(self)
        self.line_edit_search.setFixedWidth(415)
        self.line_edit_search.setPlaceholderText('Search...')
        self.line_edit_search.setStyleSheet(f'font-family: {Config.font_settings["input_font"]}; font-size: 12px;')
        self.pushbutton_next = ComponentOpsButton('\U0000f13a', self.color, parent=self)
        self.pushbutton_next.setToolTip('Next occurrence')
        self.pushbutton_prev = ComponentOpsButton('\U0000f139', self.color, parent=self)
        self.pushbutton_prev.setToolTip('Previous occurrence')
        self.pushbutton_add = ComponentOpsButton('\U000f0704', self.color, parent=self)
        self.pushbutton_add.setToolTip('Add')
        self.pushbutton_duplicate = ComponentOpsButton('\U0000f4c4', self.color, parent=self)
        self.pushbutton_duplicate.setToolTip('Duplicate')
        self.pushbutton_rename = ComponentOpsButton('\U0000f45a', self.color, parent=self)
        self.pushbutton_rename.setToolTip('Rename')
        self.pushbutton_delete = ComponentOpsButton('\U000f06f2', self.color, parent=self)
        self.pushbutton_delete.setToolTip('Delete')

        # Set up the layout
        self.setLayout(self.hlayout)
        self.hlayout.addWidget(self.label_vertical_bar)
        self.hlayout.addLayout(self.vlayout_table_top_bar)
        self.vlayout_table_top_bar.addLayout(self.hlayout_top_bar)
        self.hlayout_top_bar.addWidget(self.pushbutton_add)
        self.hlayout_top_bar.addWidget(self.pushbutton_duplicate)
        self.hlayout_top_bar.addWidget(self.pushbutton_rename)
        self.hlayout_top_bar.addWidget(self.pushbutton_delete)
        self.hlayout_top_bar.addStretch()
        self.hlayout_top_bar.addWidget(self.line_edit_search)
        self.hlayout_top_bar.addWidget(self.pushbutton_next)
        self.hlayout_top_bar.addWidget(self.pushbutton_prev)
        self.vlayout_table_top_bar.addWidget(self.component_table)

        # Disable buttons if the component is not renamable or duplicable
        if not self.sub_repo.config['class'].is_renamable:
            self.pushbutton_rename.setEnabled(False)
        if not self.sub_repo.config['class'].is_duplicable:
            self.pushbutton_duplicate.setEnabled(False)

    def _setup_action(self):
        self.pushbutton_add.clicked.connect(self.add_component)
        self.pushbutton_duplicate.clicked.connect(self.duplicate_component)
        self.pushbutton_rename.clicked.connect(self.rename_component)
        self.pushbutton_delete.clicked.connect(self.delete_component)

    def add_component(self, *args, **kwargs):
        ...

    def duplicate_component(self, *args, **kwargs):
        ...

    def rename_component(self, *args, **kwargs):
        ...

    def delete_component(self, *args, **kwargs):
        ...

    def paintEvent(self, event):
        # Draw the logo as background using the central widget as the reference
        central_widget = self.parent().parent().parent().parent()
        pos_in_central_widget = self.mapTo(central_widget, self.pos())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(0.05)
        pixmap = QPixmap(str(get_app_icon_path(256)))
        painter.drawPixmap(int(central_widget.rect().width() / 2 - pixmap.width() / 2),
                           int(central_widget.rect().height() / 2 - pixmap.height() / 2)
                           - pos_in_central_widget.y() + 20,
                           pixmap)
        painter.end()
