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

from six import binary_type, string_types, integer_types
import applescript

from .base_window import BaseWindow
from .rectangle import Rectangle


class DarwinWindow(BaseWindow):
    """
        The Window class is an interface to the macOS window control and
        placement.

    """

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
        # FIXME
        return []

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

    def _get_window_properties(self):
        cmd = '''
        tell application "System Events" to tell application process "%s"
            try
                get properties of window 1
            on error errmess
                log errmess
            end try
        end tell
        ''' % self._id
        script = applescript.AppleScript(cmd)
        properties = script.run()

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

    def _get_window_text(self):
        return self._get_window_properties()['pnam']

    def _get_class_name(self):
        return self._get_window_properties()['pcls']

    def _get_window_module(self):
        return self._id  # The window ID is the app name on macOS.

    def _get_window_pid(self):
        raise NotImplementedError()

    @property
    def is_minimized(self):
        raise NotImplementedError()

    @property
    def is_maximized(self):
        raise NotImplementedError()

    @property
    def is_visible(self):
        raise NotImplementedError()

    #-----------------------------------------------------------------------
    # Methods related to window geometry.

    def get_position(self):
        props = self._get_window_properties()
        return Rectangle(props['posn'][0], props['posn'][1],
                         props['ptsz'][0], props['ptsz'][1])

    def set_position(self, rectangle):
        assert isinstance(rectangle, Rectangle)
        raise NotImplementedError()

    #-----------------------------------------------------------------------
    # Methods for miscellaneous window control.

    def minimize(self):
        raise NotImplementedError()

    def maximize(self):
        raise NotImplementedError()

    def restore(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def set_foreground(self):
        raise NotImplementedError()
