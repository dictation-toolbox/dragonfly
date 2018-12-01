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
    if not controller_instance:
        os_controller = os_controller_class()
        os_controller.start()
        controller_instance = controller.AccessibilityController(os_controller)
    return controller_instance
