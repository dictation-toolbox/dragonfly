"""
This module initializes the accessibility controller for the current
platform.
"""

import contextlib
import os
import sys

from . import controller

from .utils import (CursorPosition, TextQuery)

# Import and set the controller class based on the current platform.
if os.environ.get("DISPLAY"):
    # Use the AT-SPI controller on X11.
    from . import atspi
    os_controller_class = atspi.Controller

elif sys.platform.startswith("win"):
    # Use the IAccessible2 controller on Windows.
    from . import ia2
    os_controller_class = ia2.Controller

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

@contextlib.contextmanager
def get_stopping_accessibility_controller():
    """Same as :func:`get_accessibility_controller`, but automatically stops when
    used in a `with` context."""

    yield get_accessibility_controller()
    if controller_instance:
        controller_instance.stop()
