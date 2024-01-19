from functools import partial

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMainWindow, QSplitter

from commons.qt_common import BSettings


class BaseWindow(QMainWindow):

    name = 'unnamed_base_window'

    minimal_size = (640, 480)
    maximal_size = (1024, 768)

    # A list of widgets that need to save and restore their state
    stateful_widgets = []
    # A dict containing the names of the event, save and load functions for each widget class
    stateful_widget_fn_dict = {
        'QSplitter': {
            'event': 'splitterMoved',
            'save_fn_name': 'saveState',
            'load_fn_name': 'restoreState',
        },
        'QTabWidget': {
            'event': 'currentChanged',
            'save_fn_name': 'currentIndex',
            'load_fn_name': 'setCurrentIndex',
        },
    }

    def __init__(self):
        super().__init__()

        self._position = self.pos()
        self._is_mouse_holding = False

        self._setup_gui()
        self._setup_action()
        self._setup_window()

    def _setup_gui(self):
        self.central_widget = QWidget(self)
        # Use Objectname to allow targeting in QSS and avoid affecting child widget styles
        self.central_widget.setObjectName('BaseWindowCentralWidget')
        self.setCentralWidget(self.central_widget)

        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(4, 4, 4, 4)

    def _setup_action(self):
        ...

    def _setup_window(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.setMinimumSize(QSize(*self.minimal_size))
        self.setMaximumSize(QSize(*self.maximal_size))

        self.settings = BSettings()
        val = self.settings.get_value(self.name, 'geometry')
        if val:
            self.restoreGeometry(val)
        else:
            self.resize(*self.minimal_size)

        self._restore_stateful_widgets()

    def _get_stateful_widget_fn_dict(self, widget):
        for class_name in self.stateful_widget_fn_dict:
            if class_name in ([cls.__name__ for cls in widget.__class__.__bases__] + [widget.__class__.__name__]):
                return self.stateful_widget_fn_dict[class_name]
        return None

    def _save_widget_state(self, widget):
        fn_dict = self._get_stateful_widget_fn_dict(widget)
        if fn_dict:
            save_fn = getattr(widget, fn_dict['save_fn_name'])

            self.settings.set_value(self.name, widget.objectName(), save_fn())

    def _register_stateful_widget(self, widget):
        assert widget.objectName(), f"Widget {widget} has no object name."
        fn_dict = self._get_stateful_widget_fn_dict(widget)
        if fn_dict:
            self.stateful_widgets.append(widget)
            event = fn_dict['event']
            getattr(widget, event).connect(partial(self._save_widget_state, widget))

    def _restore_stateful_widgets(self):
        for widget in self.stateful_widgets:
            fn_dict = self._get_stateful_widget_fn_dict(widget)
            if fn_dict:
                load_fn = getattr(widget, fn_dict['load_fn_name'])
                val = self.settings.get_value(self.name, widget.objectName())
                if val:
                    load_fn(val)

    def show(self):
        super().show()
        self.activateWindow()

    def moveEvent(self, a0):
        self.settings.set_value(self.name, 'geometry', self.saveGeometry())
        super().moveEvent(a0)

    def resizeEvent(self, a0):

        self.settings.set_value(self.name, 'geometry', self.saveGeometry())
        super().resizeEvent(a0)