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

import locale
import logging
import psutil

from six import binary_type, string_types, integer_types
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
        script = '''
        global frontApp, frontAppName
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set frontAppName to name of frontApp
            tell process frontAppName
                set mainWindow to missing value
                repeat with win in windows
                    if attribute "AXMain" of win is true then
                        set mainWindow to win
                        exit repeat
                    end if
                end repeat
            end tell
        end tell
        return frontAppName
        '''

        # window_id isn't really a unique id, instead it's just the app name
        # -- but still useful for automating through applescript
        window_id = applescript.AppleScript(script).run()
        if isinstance(window_id, binary_type):
            window_id = window_id.decode(locale.getpreferredencoding())

        return cls.get_window(id=window_id)

    @classmethod
    def get_all_windows(cls):
        script = '''
        global appIds
        tell application "System Events"
            set appIds to {}
            repeat with theProcess in (application processes)
                if not background only of theProcess then
                    set appIds to appIds & name of theProcess
                end if
            end repeat
        end tell
        return appIds
        '''
        return [cls.get_window(app_id) for app_id in
                applescript.AppleScript(script).run()]

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, id):
        BaseWindow.__init__(self, id)
        self._names.add(id)

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    def _set_id(self, id):
        if not isinstance(id, (string_types, integer_types)):
            raise TypeError("Window id/handle must be an int or string,"
                            " but received {0!r}".format(id))
        self._id = id
        self._windows_by_id[id] = self

    #-----------------------------------------------------------------------
    # Methods and properties for window attributes.

    def get_properties(self):
        """
        Method to get the properties of a macOS window.

        :rtype: dict
        :returns: window properties
        """
        script = '''
        tell application "System Events" to tell application process "%s"
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
        ''' % (self._id, attribute)
        return applescript.AppleScript(script).run()

    def _get_window_text(self):
        return self.get_properties().get('pnam', '')

    def _get_class_name(self):
        return self.get_properties().get('pcls', '')

    def _get_window_module(self):
        return self._id  # The window ID is the app name on macOS.

    def _get_window_pid(self):
        if not (self._id and isinstance(self._id, string_types)):
            # Can't match against numerical / empty / null app bundle ID.
            return -1

        for process in psutil.process_iter(attrs=['pid', 'exe']):
            exe = process.info['exe']
            if exe and exe.endswith(self._id):
                # Return the ID of the first matching process.
                return process.info['pid']

        # No match.
        return -1

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
            set firstWindow to first window of application process "%s"
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
            first window of process "%s"
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
        tell application "%s"
            activate window 1
        end tell
        ''' % self._id
        applescript.AppleScript(script).run()
