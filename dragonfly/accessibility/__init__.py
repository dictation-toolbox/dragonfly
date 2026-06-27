"""
This module initializes the accessibility controller for the current
platform.
"""

import contextlib
import importlib
import logging
import os
import sys

from . import controller

from .utils import (CursorPosition, TextQuery)

_log = logging.getLogger("accessibility")


def _load_controller_classes(*module_names):
    controller_classes = []
    for module_name in module_names:
        try:
            module = importlib.import_module("." + module_name, __name__)
        except ImportError:
            continue
        controller_class = getattr(module, "Controller", None)
        if controller_class:
            controller_classes.append(controller_class)
    return controller_classes

# Import and set the controller class based on the current platform.
# Note: dragonfly._platform_checks is not used here in an effort to keep the
#  accessibility sub-package modular.
#  Please see the module docstring of utils.py.
#
if ":" in os.environ.get("DISPLAY", ""):
    # Use the AT-SPI controller on X11.
    os_controller_classes = _load_controller_classes("atspi")

elif sys.platform.startswith("win"):
    # Prefer UIA on Windows and keep IA2 as a fallback.
    os_controller_classes = _load_controller_classes("uia", "ia2")

else:
    os_controller_classes = []

controller_instance = None


def get_accessibility_controller():
    """Get the OS-independent accessibility controller which is the gateway to all
    accessibility functionality. Returns None if OS is not supported."""

    global controller_instance
    if (not controller_instance or controller_instance.stopped):
        controller_instance = None
        for os_controller_class in os_controller_classes:
            try:
                os_controller = os_controller_class()
                controller_instance = controller.AccessibilityController(os_controller)
                break
            except Exception as exception:
                _log.debug("Failed to initialize %s: %s" %
                           (os_controller_class, exception))
    return controller_instance


@contextlib.contextmanager
def get_stopping_accessibility_controller():
    """Same as :func:`get_accessibility_controller`, but automatically stops when
    used in a `with` context."""

    yield get_accessibility_controller()
    if controller_instance:
        controller_instance.stop()
