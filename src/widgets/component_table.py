import math

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QLabel, QSizePolicy

from commons.color import BColors
from widgets.component_item import ComponentItemWidgetManager


class ComponentTableWidget(QTableWidget):

    def __init__(self, setting_dict, sub_repo, parent=None):
        super().__init__(parent)
        self.setting_dict = setting_dict
        self.name = self.setting_dict['name']
        self.color = self.setting_dict['color']
        self.item_size_hint = self.setting_dict['table_item_size_hint']
        self.setObjectName('ComponentTable' + self.name.title().replace('_', ''))
        self.sub_repo = sub_repo

        self._setup_gui()
        self._setup_action()
        self.setup_items()

    def _setup_gui(self):
        self.setContentsMargins(0, 0, 0, 0)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet('border: 0px; background: transparent;')

    def _setup_action(self):
        ...

    def setup_items(self):
        self.component_items = [ComponentItemWidgetManager.create(component, self)
                                for component in self.sub_repo.pool.values()]

    def _get_row_column_count(self) -> (int, int):
        # Column count is determined by the width of the viewport
        column_count = self.viewport().width() // self.item_size_hint[0]
        # Row count is determined by the number of items in the pool
        row_count = math.ceil(len(self.sub_repo.pool) / column_count)
        return row_count, column_count

    def setup_grid(self):
        row_count, column_count = self._get_row_column_count()
        self.setColumnCount(column_count)
        self.setRowCount(row_count)

        for i in range(self.rowCount()):
            self.setRowHeight(i, self.item_size_hint[1])
        for j in range(self.columnCount()):
            self.setColumnWidth(j, self.viewport().width() // self.columnCount())

        for i, component_item in enumerate(self.component_items):
            row = i // column_count
            col = i % column_count
            self.setCellWidget(row, col, component_item)  # Corrected placement

    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        padding, selection_padding = 2, 3
        width = int(self.viewport().width() / self.columnCount())
        height = self.item_size_hint[1]
        painter.setPen(QColor(BColors.sub_text.value))
        painter.setOpacity(0.2)
        selection_pen = QPen(QColor(self.color))
        selection_pen.setWidth(2)
        selection_pen.setStyle(Qt.PenStyle.DotLine)
        # Draw the cell borders
        for i in range(self.viewport().height() // height + 1):
            for j in range(self.columnCount()):
                rect = QRect(j * width + padding, i * height + padding,
                             width - padding * 2 - 1, height - padding * 2 - 1)
                painter.drawRect(rect)
        # Draw the selection border
        for index in self.selectedIndexes():

            i, j = index.row(), index.column()
            if self.cellWidget(i, j):
                painter.setPen(selection_pen)
                painter.setOpacity(1.0)
                selection_rect = QRect(j * width + selection_padding, i * height + selection_padding,
                                       width - selection_padding * 2 - 1, height - selection_padding * 2 - 1)
                painter.drawRect(selection_rect)

    def showEvent(self, event):
        self.setup_grid()  # This is when the actual size of the widget is known
        event.accept()

    def resizeEvent(self, event):
        self.setup_grid()
        event.accept()