from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QSplitter, QSplitterHandle

from commons.colors import MonokaiColors


class SplitterHandler(QSplitterHandle):
    """Custom splitter bar drawing class for the Terrain Layer Editor window."""

    splitter_bar_width = 100

    def __init__(self, orientation: Qt.Orientation, parent=None):
        super().__init__(orientation, parent)

    def sizeHint(self):
        return QSize(12, 12)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(MonokaiColors.comment.value), 1, Qt.PenStyle.DotLine))
        if self.orientation() == Qt.Orientation.Vertical:
            yPos = int(event.rect().height() / 2 - 1)
            start = int(max(0, event.rect().width() / 2 - self.splitter_bar_width))
            end = int(min(event.rect().right(), event.rect().width() / 2 + self.splitter_bar_width))
            painter.drawLine(start, yPos, end, yPos)
            yPos = int(event.rect().height() / 2 + 1)
            painter.drawLine(start, yPos, end, yPos)
        else:
            xPos = int(event.rect().width() / 2 - 1)
            start = int(max(0, event.rect().height() / 2 - self.splitter_bar_width))
            end = int(min(event.rect().bottom(), event.rect().height() / 2 + self.splitter_bar_width))
            painter.drawLine(xPos, start, xPos, end)
            xPos = int(event.rect().width() / 2 + 1)
            painter.drawLine(xPos, start, xPos, end)


class Splitter(QSplitter):
    """Custom splitter class for the Terrain Layer Editor window."""

    def __init__(self, orientation: Qt.Orientation, parent=None):
        super().__init__(parent)
        self.setOrientation(orientation)

    def createHandle(self):
        return SplitterHandler(self.orientation(), self)
