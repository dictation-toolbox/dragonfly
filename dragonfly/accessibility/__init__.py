from contextlib import contextmanager
import sys

from . import controller

from .utils import (CursorPosition, TextQuery)

if sys.platform.startswith("win"):
    from . import ia2
    os_controller_class = ia2.Controller
elif sys.platform.startswith("linux"):
    from . import atspi
    os_controller_class = atspi.Controller
else:
    os_controller_class = None

controller_instance = None

def get_accessibility_controller():
    """Get the OS-independent accessibility controller which is the gateway to all
    accessibility functionality. Returns None if OS is not supported."""

    global controller_instance
    if os_controller_class and (not controller_instance or controller_instance.stopped):
        os_controller = os_controller_class()
        controller_instance = controller.AccessibilityController(os_controller)
    return controller_instance

@contextmanager
def get_stopping_accessibility_controller():
    """Same as :func:`get_accessibility_controller`, but automatically stops when
    used in a `with` context."""

    yield get_accessibility_controller()
    if controller_instance:
        controller_instance.stop()
