import sys

from PyQt6.QtWidgets import QApplication

from commons.qt_common import apply_stylesheet
from config import Config
from windows.main_window import MainWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    apply_stylesheet(app)
    app.setApplicationName(Config.app_name)
    app.setApplicationVersion(str(Config.app_version))
    app.setQuitOnLastWindowClosed(True)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
