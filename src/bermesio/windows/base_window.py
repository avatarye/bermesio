import types
from functools import partial

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMainWindow, QButtonGroup

from bermesio.commons.qt_common import BSettings


class BaseWindow(QMainWindow):
    """
    A base class for all windows in the application. This class mainly handles the fundamental window functionalities
    including settings, save and restore state, and more.
    It uses a mechanism to simplify the process of saving and restoring state of widgets. The widgets need to meet 3
    requirements:
    1. The widget must have a unique ObjectName defined.
    2. The widget needs to be added to the stateful_widgets list using self._register_stateful_widget() fn
    3. The widget's class or super class needs to be added to the stateful_widget_fn_dict dict with the names of
       the triggering event, save and load functions.
    """

    # The name of the window, used to save and restore settings in its own child level
    name = 'UnnamedBaseWindow'

    minimal_size = (640, 280)
    maximal_size = (1024, 768)

    # A list of widgets that need to save and restore their state
    stateful_widgets = []
    # A dict containing the names of the event and save function, and a lambda as load function for each widget class.
    # NOTE: The lambda function must take the widget as the first argument and the value as the second argument.
    stateful_widget_fn_dict = {
        'QSplitter': {
            'event': 'splitterMoved',
            'save_fn_name': 'saveState',
            'load_fn_name': lambda widget, val: widget.restoreState(val),
        },
        'QTabWidget': {
            'event': 'currentChanged',
            'save_fn_name': 'currentIndex',
            'load_fn_name': lambda widget, val: widget.setCurrentIndex(val),
        },
        'QStackedWidget': {
            'event': 'currentChanged',
            'save_fn_name': 'currentIndex',
            'load_fn_name': lambda widget, val: widget.setCurrentIndex(val),
        },
        'QPushButton': {
            'event': 'clicked',
            'save_fn_name': 'isChecked',
            'load_fn_name': lambda widget, val: widget.setChecked(val),
        },
        'QButtonGroup': {
            'event': 'buttonClicked',
            'save_fn_name': 'checkedId',
            'load_fn_name': lambda widget, val: widget.button(val).setChecked(True),
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
        # Set window to be frameless and delete on close
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.setMinimumSize(QSize(*self.minimal_size))
        self.setMaximumSize(QSize(*self.maximal_size))

        self.settings = BSettings()
        val = self.settings.get_value(self.name, 'Geometry')
        if val:
            self.restoreGeometry(val)
        else:
            self.resize(*self.minimal_size)

        self._restore_stateful_widgets()

    def _get_stateful_widget_fn_dict(self, widget):
        """
        Get the stateful widget function dict for the given widget based on its class. Handles same class or subclass
        cases.
        """
        for class_name in self.stateful_widget_fn_dict:
            if class_name in ([cls.__name__ for cls in widget.__class__.__bases__] + [widget.__class__.__name__]):
                return self.stateful_widget_fn_dict[class_name]
        return None

    def _register_stateful_widget(self, widget):
        assert widget.objectName(), f'Widget {widget} has no object name.'
        fn_dict = self._get_stateful_widget_fn_dict(widget)
        assert fn_dict, f'Widget {widget}\'s class is not defined in stateful_widget_fn_dict.'
        self.stateful_widgets.append(widget)
        event = fn_dict['event']
        getattr(widget, event).connect(partial(self._save_stateful_widget, widget))

    def _save_stateful_widget(self, widget):
        fn_dict = self._get_stateful_widget_fn_dict(widget)
        assert fn_dict, f'Widget {widget}\'s class is not defined in stateful_widget_fn_dict.'
        save_fn = getattr(widget, fn_dict['save_fn_name'])
        self.settings.set_value(self.name, widget.objectName(), save_fn())

    def _restore_stateful_widgets(self):
        # Handle boolean values because QSettings only supports string values
        val_mapping_dict = {'true': True, 'false': False,}
        for widget in self.stateful_widgets:
            fn_dict = self._get_stateful_widget_fn_dict(widget)
            assert fn_dict, f'Widget {widget}\'s class is not defined in stateful_widget_fn_dict.'
            val = self.settings.get_value(self.name, widget.objectName())
            val = val_mapping_dict.get(val, val)
            if val:
                restore_fn = fn_dict['load_fn_name']
                restore_fn(widget, val)

    def show(self):
        super().show()
        self.activateWindow()
        self.raise_()

    def moveEvent(self, a0):
        self.settings.set_value(self.name, 'Geometry', self.saveGeometry())
        super().moveEvent(a0)

    def resizeEvent(self, a0):
        self.settings.set_value(self.name, 'Geometry', self.saveGeometry())
        super().resizeEvent(a0)
