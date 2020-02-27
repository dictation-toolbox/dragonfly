# coding=utf-8
#
# This file is part of Aenea
#
# Aenea is free software: you can redistribute it and/or modify it under
# the terms of version 3 of the GNU Lesser General Public License as
# published by the Free Software Foundation.
#
# Aenea is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with Aenea.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (2014) Alex Roper
# Alex Roper <alex@aroper.net>
#
# Modified from Aenea's server_osx.py file.

"""
Window class for macOS
============================================================================

"""

# pylint: disable=E0401
# This file imports MacOS-only symbols.

# pylint: disable=W0622
# Suppress warnings about redefining the built-in 'id' function.

import locale
import logging
import os

from six import binary_type
import applescript

from .base_window import BaseWindow
from .rectangle import Rectangle


class DarwinWindow(BaseWindow):
    """
        The Window class is an interface to the macOS window control and
        placement.

    """

    _log = logging.getLogger("window")

    #-----------------------------------------------------------------------
    # Class methods to create new Window objects.

    @classmethod
    def get_foreground(cls):
        script = u'''
        global theId
        tell application "System Events"
            set theId to id of first application process whose ¬
            frontmost is true
        end tell
        return theId
        '''
        window_id = applescript.AppleScript(script).run()
        if isinstance(window_id, binary_type):
            window_id = window_id.decode(locale.getpreferredencoding())

        return cls.get_window(id=int(window_id))

    @classmethod
    def get_matching_windows(cls, executable=None, title=None):
        # Convert absolute executable paths to basenames on macOS. This is
        # necessary because DarwinWindow executable names are not absolute
        # and will therefore never match.
        if executable is not None and os.path.isabs(executable):
            executable = os.path.basename(executable)

        return super(DarwinWindow, cls).get_matching_windows(
            executable, title
        )

    @classmethod
    def get_all_windows(cls):
        script = u'''
        global appIds
        tell application "System Events"
            set appIds to id of every application process whose ¬
            background only is false
        end tell
        return appIds
        '''
        return [cls.get_window(int(app_id)) for app_id in
                applescript.AppleScript(script).run()]

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, id):
        BaseWindow.__init__(self, id)
        self._names.add(str(id))

    #-----------------------------------------------------------------------
    # Methods and properties for window attributes.

    def get_properties(self):
        """
        Method to get the properties of a macOS window.

        :rtype: dict
        :returns: window properties
        """
        script = '''
        tell application "System Events" to tell application process id "%s"
            try
                get properties of window 1
            on error errmess
                log errmess
            end try
        end tell
        ''' % self._id
        properties = applescript.AppleScript(script).run()
        if not properties:
            return {}

        result = {}
        encoding = locale.getpreferredencoding()
        for key, value in properties.items():
            key = key.code
            if isinstance(key, binary_type):
                key = key.decode(encoding)
            if isinstance(value, applescript.AEType):
                value = value.code
                if isinstance(value, binary_type):
                    value = value.decode(encoding)
            result[key] = value
        return result

    def get_attribute(self, attribute):
        """
        Method to get an attribute of a macOS window.

        **Note**: this method doesn't distinguish between multiple instances
        of the same application.

        :param attribute: attribute name
        :type attribute: string
        :returns: attribute value
        """
        script = '''
        tell application "%s"
            try
                get %s of window 1
            on error errmess
                log errmess
            end try
        end tell
        ''' % (self.executable, attribute)
        return applescript.AppleScript(script).run()

    def _get_window_text(self):
        return self.get_properties().get('pnam', '')

    def _get_class_name(self):
        return self.get_properties().get('pcls', '')

    def _get_window_module(self):
        script = '''
        global module
        set module to ""
        try
            tell application "System Events" to tell application process id %s
                set module to name
            end tell
        end try
        return module
        ''' % (self._id)
        return applescript.AppleScript(script).run()

    def _get_window_pid(self):
        script = '''
        global pid
        set pid to -1
        try
            tell application "System Events" to tell application process id %s
                set pid to unix id
            end tell
        end try
        return pid
        ''' % (self._id)
        return applescript.AppleScript(script).run()

    @property
    def is_minimized(self):
        return self.get_attribute('miniaturized')

    @property
    def is_maximized(self):
        return self.get_attribute('zoomed')

    @property
    def is_visible(self):
        return self.get_attribute('visible')

    #-----------------------------------------------------------------------
    # Methods related to window geometry.

    def get_position(self):
        props = self.get_properties()
        return Rectangle(props['posn'][0], props['posn'][1],
                         props['ptsz'][0], props['ptsz'][1])

    def set_position(self, rectangle):
        assert isinstance(rectangle, Rectangle)
        script = '''
        tell application "System Events"
            set firstWindow to first window of application process id "%s"
            set position of firstWindow to {%d, %d}
            set size of firstWindow to {%d, %d}
        end tell
        ''' % (self._id, rectangle.x, rectangle.y, rectangle.dx,
               rectangle.dy)
        applescript.AppleScript(script).run()

    #-----------------------------------------------------------------------
    # Methods for miscellaneous window control.

    def _press_window_button(self, button_subrole, action):
        # Note: The negation symbol ¬ is used to split long lines in
        # AppleScript.
        script = u'''
        tell application "System Events"
            perform action "%s" of (first button whose subrole is "%s") of ¬
            first window of application process id "%s"
        end tell
        ''' % (action, button_subrole, self._id)
        try:
            applescript.AppleScript(script).run()
            return True
        except applescript.ScriptError as err:
            self._log.error("Failed to perform window button action "
                            "%s -> %s: %s", button_subrole, action, err)
            return False

    def minimize(self):
        return self._press_window_button("AXMinimizeButton", "AXPress")

    def maximize(self):
        return self._press_window_button("AXFullScreenButton",
                                         "AXZoomWindow")

    def full_screen(self):
        """
        Enable full screen mode for this window.

        **Note**: this doesn't allow transitioning out of full screen mode.
        """
        return self._press_window_button("AXFullScreenButton", "AXPress")

    def restore(self):
        # Toggle maximized/minimized state if necessary.
        if self.is_maximized:
            return self.maximize()

        if self.is_minimized:
            return self.minimize()

        return True

    def close(self):
        return self._press_window_button("AXCloseButton", "AXPress")

    def set_foreground(self):
        script = '''
        tell application "System Events" to tell application process id "%s"
            set frontmost to true
        end tell
        ''' % self._id
        applescript.AppleScript(script).run()

    def set_focus(self):
        # Setting window focus without raising the window doesn't appear to
        # be possible in macOS, so fallback on set_foreground().
        self.set_foreground()
