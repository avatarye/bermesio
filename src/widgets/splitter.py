from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QSplitter, QSplitterHandle

from commons.color import MonokaiColors


class SplitterHandler(QSplitterHandle):
    """A custom splitter handler class for mostly handling the drawing of the splitter bar."""

    splitter_bar_width = 100

    def __init__(self, orientation: Qt.Orientation, parent=None):
        super().__init__(orientation, parent)

    def sizeHint(self):
        return QSize(12, 12)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(MonokaiColors.comment.value), 1, Qt.PenStyle.DotLine))
        if self.orientation() == Qt.Orientation.Vertical:
            pos_y = int(event.rect().height() / 2 - 1)
            start = int(max(0, event.rect().width() / 2 - self.splitter_bar_width))
            end = int(min(event.rect().right(), event.rect().width() / 2 + self.splitter_bar_width))
            painter.drawLine(start, pos_y, end, pos_y)
            pos_y = int(event.rect().height() / 2 + 1)
            painter.drawLine(start, pos_y, end, pos_y)
        else:
            pos_x = int(event.rect().width() / 2 - 1)
            start = int(max(0, event.rect().height() / 2 - self.splitter_bar_width))
            end = int(min(event.rect().bottom(), event.rect().height() / 2 + self.splitter_bar_width))
            painter.drawLine(pos_x, start, pos_x, end)
            pos_x = int(event.rect().width() / 2 + 1)
            painter.drawLine(pos_x, start, pos_x, end)


class Splitter(QSplitter):
    """A custom splitter class for mostly handling the drawing of the splitter bar."""

    def __init__(self, orientation: Qt.Orientation, parent=None):
        super().__init__(parent)
        self.setOrientation(orientation)

    def createHandle(self):
        return SplitterHandler(self.orientation(), self)
