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

"""
WaitWindow action -- wait for a specific window context
============================================================================

"""


import time
import win32con
from dragonfly.actions.action_base import ActionBase, ActionError
from dragonfly.windows.window import Window


#---------------------------------------------------------------------------

class WaitWindow(ActionBase):
    """
        Wait for a specific window context action.

        Constructor arguments:
         - *title* (*str*) --
           part of the window title: not case sensitive
         - *executable* (*str*) --
           part of the file name of the executable; not case sensitive
         - *timeout* (*int* or *float*) --
           the maximum number of seconds to wait for the correct
           context, after which an :class:`ActionError` will
           be raised.

        When this action is executed, it waits until the correct window 
        context is present.  This window context is specified by the 
        desired window title of the foreground window and/or the 
        executable name of the foreground application.  These are 
        specified using the constructor arguments listed above.  The 
        substring search used is *not* case sensitive.

        If the correct window context is not found within *timeout* 
        seconds, then this action will raise an :class:`ActionError` to 
        indicate the timeout.

    """

    def __init__(self, title=None, executable=None,
                 timeout=15):
        self._match_functions = []
        string = []

        if title is not None:
            self._title = title.lower()
            self._match_functions.append("_match_title")
            string.append("title=%r" % self._title)
        else:
            self._title = None

        if executable is not None:
            self._executable = executable.lower()
            self._match_functions.append("_match_executable")
            string.append("executable=%r" % self._executable)
        else:
            self._executable = None

        self._timeout = timeout

        ActionBase.__init__(self)
        self._str = ", ".join(string)

    def _execute(self, data=None):
        self._log.debug("Waiting for window context: %s" % self)
        start_time = time.time()
        while 1:
            foreground = Window.get_foreground()
            mismatch = False
            for match_name in self._match_functions:
                match_func = getattr(self, match_name)
                if not match_func(foreground):
                    mismatch = True
                    break
            if not mismatch:
                return
            if time.time() - start_time > self._timeout:
                raise ActionError("Timeout while waiting for window context: %s" % self)

    def _match_title(self, foreground):
        if self._title is None:
            return True
        current_title = foreground.title.lower()
        if current_title.find(self._title) != -1:
            return True
        return False

    def _match_executable(self, foreground):
        if self._executable is None:
            return True
        current_executable = foreground.executable.lower()
        if current_executable.find(self._executable) != -1:
            return True
        return False
