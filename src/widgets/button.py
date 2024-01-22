from PyQt6.QtWidgets import QPushButton

from commons.color import BColors
from config import Config


class GlyphIconButton(QPushButton):

    def __init__(self, glyph_icon, color, font=None, parent=None):
        super().__init__(glyph_icon, parent)
        self.color = color
        if font is None:
            self.font = Config.font_settings['glyph_icon_font']
        else:
            self.font = font
        self.setStyleSheet("""
            QPushButton {
                border: 0px solid %s;
                background-color: transparent;
                color: %s;
                font-size: 20px;
                font-family: %s;
            }
            QPushButton:hover {
                color: %s;
            }
        """ % (BColors.sub_text.value, self.color, self.font, BColors.text.value))


class ComponentOpsButton(GlyphIconButton):

    def __init__(self, glyph_icon, color, parent=None):
        super().__init__(glyph_icon, color, parent=parent)
        self.setFixedSize(24, 24)
