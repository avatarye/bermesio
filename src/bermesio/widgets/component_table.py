import math

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtWidgets import QTableWidget

from bermesio.commons.color import BColors
from bermesio.commons.qt_singal import SIGNAL
from bermesio.widgets.component_item import ComponentItemWidgetManager


class ComponentTableWidget(QTableWidget):
    """
    A subclass of QTableWidget that is used as a component table in the main window's stack widget.
    The process of setting up the table is a bit complicated due to the dynamic nature of the table.
    1. The initial setup is triggered by emitting SIGNAL.load_sub_repo with this sub_repo. Using signal instead of
       calling the method is to allow other function to trigger the setup as well when the sub_repo is changed.
    2. The signal is connected to setup_items method, which creates the component items from the sub_repo and stores
       them in a list and flags the table to be setup in the next paint event.
    3. The paint event checks if the table is flagged to be setup, if yes, it calls the setup_table method to set up the
       table, including row and column count, row height and column width, and adding the component items to the table.
    4. The resizing event also uses this mechanism to flag the table to be setup in the next paint event to achieve the
       dynamic resizing of the table.
    """

    def __init__(self, component_setting_dict, sub_repo, parent=None):
        super().__init__(parent)
        self.component_setting_dict = component_setting_dict
        self.name = self.component_setting_dict['name']
        self.color = self.component_setting_dict['color']
        self.item_size_hint = self.component_setting_dict['table_item_size_hint']
        self.setObjectName('ComponentTable' + self.name.title().replace('_', ''))
        self.sub_repo = sub_repo

        self.if_to_setup_table = False

        self._setup_gui()
        self._setup_action()
        # Emit the signal with self.sub_repo as the argument to trigger the setup_items method which loads the items
        # into the table. Other functions may emit this signal as well for other table to load or update, so attaching
        # the sub_repo to distinguish between the tables.
        SIGNAL.load_sub_repo.emit(self.sub_repo)

    def _setup_gui(self):
        self.setContentsMargins(0, 0, 0, 0)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet('border: 0px; background: transparent;')

    def _setup_action(self):
        SIGNAL.load_sub_repo.connect(self._setup_items)

        self.cellDoubleClicked.connect(self._load_component_in_editor)

    def _setup_items(self, sub_repo):
        # Check if the signal is intended for this table
        if sub_repo is self.sub_repo:
            self.component_items = [ComponentItemWidgetManager.create(component, self)
                                    for component in self.sub_repo.pool.values()]
            # Flag the table to be setup in the next paint event since the items have been changed. This is the main way
            # to update the table.
            self.if_to_setup_table = True

    def _setup_table(self):

        def get_row_column_count() -> (int, int):
            # Column count is determined by the width of the viewport
            column_count = max(1, self.viewport().width() // self.item_size_hint[0])
            # Row count is determined by the number of items in the pool
            row_count = max(1, math.ceil(len(self.sub_repo.pool) / column_count))
            return row_count, column_count

        row_count, column_count = get_row_column_count()
        self.setColumnCount(column_count)
        self.setRowCount(row_count)

        for i in range(self.rowCount()):
            self.setRowHeight(i, self.item_size_hint[1])
        for j in range(self.columnCount()):
            self.setColumnWidth(j, self.viewport().width() // self.columnCount())

        for i, component_item in enumerate(self.component_items):
            row = i // column_count
            col = i % column_count
            self.setCellWidget(row, col, component_item)

        # After the table is set up, flag the table to not be setup in the next paint event
        self.if_to_setup_table = False

    def _load_component_in_editor(self, row, column):
        # Check if the component is editable, if yes, emit the signal to load the component in the editor
        if self.sub_repo.config['class'].is_editable:
            component = self.cellWidget(row, column).component
            assert component, f'Component at row {row} and column {column} is None.'
            SIGNAL.load_component_in_editor.emit(component)

    def paintEvent(self, event):
        if self.if_to_setup_table:  # The main way to update the table layout dynamically
            self._setup_table()
        painter = QPainter(self.viewport())
        padding, selection_padding = 2, 3
        width = int(self.viewport().width() / self.columnCount())
        height = self.item_size_hint[1]
        painter.setPen(QColor(BColors.sub_text.value))
        painter.setOpacity(0.2)
        selection_pen = QPen(QColor(self.color))
        selection_pen.setWidth(2)
        selection_pen.setStyle(Qt.PenStyle.DotLine)
        # Draw the cell borders and fill background if there is a widget
        for i in range(self.viewport().height() // height + 1):
            for j in range(self.columnCount()):
                rect = QRect(j * width + padding, i * height + padding,
                             width - padding * 2 - 1, height - padding * 2 - 1)
                painter.setOpacity(0.05)
                if self.cellWidget(i, j):
                    painter.fillRect(rect, QColor(self.color))
                painter.setOpacity(0.2)
                painter.drawRect(rect)
        # Draw the selection borders
        for index in self.selectedIndexes():
            i, j = index.row(), index.column()
            if self.cellWidget(i, j):
                painter.setPen(selection_pen)
                painter.setOpacity(1.0)
                selection_rect = QRect(j * width + selection_padding, i * height + selection_padding,
                                       width - selection_padding * 2 - 1, height - selection_padding * 2 - 1)
                painter.drawRect(selection_rect)

    def resizeEvent(self, e):
        """
        Override the resize event to dynamically resize the table columns and rows based on the component item number
        and its size hint.

        :param e: The resize event
        """
        self.if_to_setup_table = True
        super().resizeEvent(e)