import sys

from PyQt6.QtWidgets import QApplication

from config import Config


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName(Config.app_name)
    app.setApplicationVersion(Config.app_version)
    app.setQuitOnLastWindowClosed(False)

    # Launch the application
    sys.exit()
