#
# This file is part of Dragonfly.
# (c) Copyright 2007, 2008 by Christo Butcher
# Licensed under the LGPL.
#
#   Dragonfly is free software: you can redistribute it and/or modify it
#   under the terms of the GNU Lesser General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Dragonfly is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public
#   License along with Dragonfly.  If not, see
#   <http://www.gnu.org/licenses/>.
#

# pylint: disable=W0603
# Suppress warnings about global statements used for configuration.

# pylint: disable=E1111
# Implementations of BaseKeyboardAction return different types for events.

import io
import os
from os.path import basename
import sys

from .action_base  import DynStrActionBase
from .keyboard     import Keyboard


UNICODE_KEYBOARD = False
HARDWARE_APPS = [
    "tvnviewer.exe", "vncviewer.exe", "mstsc.exe", "virtualbox.exe"
]
PAUSE_DEFAULT = 0.005


def load_configuration():
    """Locate and load configuration."""
    try:
        import configparser
    except ImportError:
        import ConfigParser as configparser

    global UNICODE_KEYBOARD
    global HARDWARE_APPS
    global PAUSE_DEFAULT

    home = os.path.expanduser("~")
    config_folder = os.path.join(home, ".dragonfly2-speech")
    config_file = "settings.cfg"
    config_path = os.path.join(config_folder, config_file)

    if not os.path.exists(config_folder):
        os.mkdir(config_folder)
    if not os.path.exists(config_path):
        with io.open(config_path, "w") as f:
            # Write the default values to the config file.
            f.write(u'[Text]\n')
            f.write(u'hardware_apps = %s\n' % "|".join(HARDWARE_APPS))
            f.write(u'unicode_keyboard = %s\n' % UNICODE_KEYBOARD)
            f.write(u'pause_default = %f\n' % PAUSE_DEFAULT)

    parser = configparser.ConfigParser()
    parser.read(config_path)
    if parser.has_option("Text", "hardware_apps"):
        HARDWARE_APPS = parser.get("Text", "hardware_apps").lower().split("|")
    if parser.has_option("Text", "unicode_keyboard"):
        UNICODE_KEYBOARD = parser.getboolean("Text", "unicode_keyboard")
    if parser.has_option("Text", "pause_default"):
        PAUSE_DEFAULT = parser.getfloat("Text", "pause_default")


load_configuration()


class BaseKeyboardAction(DynStrActionBase):
    """
        Base keystroke emulation action.

        This class isn't meant to be used directly.

    """

    _keyboard = Keyboard()
    _pause_default = PAUSE_DEFAULT

    def __init__(self, spec=None, static=False, use_hardware=False):
        # Note: these are only used on Windows.
        self._event_cache = {}
        self._use_hardware = use_hardware

        super(BaseKeyboardAction, self).__init__(spec, static)

        # Save events for the current layout if on Windows.
        if self._events is not None and sys.platform.startswith("win"):
            layout = self._keyboard.get_current_layout()
            self._event_cache[layout] = self._events

    def require_hardware_events(self):
        """
        Return `True` if the current context requires hardware emulation.
        """
        # Always use hardware_events for non-Windows platforms.
        if not sys.platform.startswith("win") or self._use_hardware:
            return True

        # Otherwise check if hardware events should be used with the current
        # foreground window.
        from dragonfly.windows import Window
        foreground_executable = basename(Window.get_foreground()
                                         .executable.lower())
        return ((not UNICODE_KEYBOARD) or
                (foreground_executable in HARDWARE_APPS))

    def _execute(self, data=None):
        # Get updated events on Windows for each new keyboard layout
        # encountered.
        if sys.platform.startswith("win") and self._static:
            layout = self._keyboard.get_current_layout()
            events = self._event_cache.get(layout)
            if events is None:
                self._events = self._parse_spec(self._spec)
                self._event_cache[layout] = self._events

        return super(BaseKeyboardAction, self)._execute(data)
