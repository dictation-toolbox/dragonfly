from contextlib import contextmanager
import sys

from . import controller

from .utils import (CursorPosition, TextQuery)

if sys.platform.startswith("win"):
    from . import ia2
    os_controller_class = ia2.Controller
else:
    # TODO Support Linux.
    pass

controller_instance = None

def get_accessibility_controller():
    """Get the OS-independent accessibility controller which is the gateway to all
    accessibility functionality."""

    global controller_instance
    if not controller_instance or controller_instance.stopped:
        os_controller = os_controller_class()
        controller_instance = controller.AccessibilityController(os_controller)
    return controller_instance

@contextmanager
def get_stopping_accessibility_controller():
    """Same as :func:`get_accessibility_controller`, but automatically stops when
    used in a `with` context."""

    yield get_accessibility_controller()
    controller_instance.stop()
