from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QPainter, QFont, QColor, QPen, QFontMetrics
from PyQt6.QtCore import Qt, QRect

from commons.colors import BColors


class ComponentButton(QPushButton):

    def __init__(self, text, icon_char, color, parent=None):
        super().__init__(text, parent)
        self.hover = False
        self.text, self.icon_char, self.color = text, icon_char, color
        self.glyph_icon_font = QFont("JetBrainsMono NFP", 12)
        self.text_font = QFont("Open Sans SemiCondensed", 10)
        self.text_font.setBold(True)
        self.spacing = 4
        self.padding = 6
        self.setFixedHeight(24)
        self.setFixedWidth(self._get_button_width())

    def _get_button_width(self) -> int:
        glyph_metrics = QFontMetrics(self.glyph_icon_font)
        self.glyph_icon_width = glyph_metrics.horizontalAdvance(self.icon_char)
        text_metrics = QFontMetrics(self.text_font)
        self.text_width = text_metrics.horizontalAdvance(self.text)
        return self.glyph_icon_width + self.text_width + self.spacing + self.padding * 2

    def paintEvent(self, event):
        painter = QPainter(self)
        # Set background color based on checked state
        if self.isChecked():
            painter.fillRect(self.rect(), QColor(self.color))
        else:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        # Set color based on hover state
        if self.hover:
            painter.setPen(QColor(BColors.text.value))
        else:
            if self.isChecked():
                painter.setPen(QColor(BColors.background.value))
            else:
                painter.setPen(QColor(self.color))
        rect = QRect(self.padding, 2, self.width(), self.height())
        # Draw glyph
        painter.setFont(self.glyph_icon_font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft, self.icon_char)
        # Draw text
        painter.setFont(self.text_font)
        rect.setX(self.padding + self.glyph_icon_width + self.spacing)
        rect.setY(3)
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft, self.text)
        # Draw border
        border_pen = QPen(QColor(BColors.sub_text.value), 1)
        painter.setPen(border_pen)
        border_rect = QRect(0, 0, self.width() - 1, self.height() - 1)
        painter.drawRect(border_rect)

    def enterEvent(self, event):
        self.hover = True
        self.update()

    def leaveEvent(self, event):
        self.hover = False
        self.update()
