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
FocusWindow action -- bring a window to the foreground
============================================================================

"""


import win32con
from .action_base      import ActionBase, ActionError
from ..windows.window  import Window


#---------------------------------------------------------------------------

class FocusWindow(ActionBase):
    """
        Bring a window to the foreground action.

        Constructor arguments:
         - *executable* (*str*) -- part of the filename of the
           application's executable to which the target window belongs;
           not case sensitive.
         - *title* (*str*) -- part of the title of the target window;
           not case sensitive.

        This action searches all visible windows for a window which 
        matches the given parameters.

    """

    def __init__(self, executable=None, title=None):
        if executable:  self.executable = executable.lower()
        else:           self.executable = None
        if title:       self.title = title.lower()
        else:           self.title = None
        ActionBase.__init__(self)

        arguments = []
        if executable:  arguments.append("executable=%r" % executable)
        if title:       arguments.append("title=%r" % title)
        self._str = ", ".join(arguments)

    def _execute(self, data=None):
        executable = self.executable
        title = self.title
        if data and isinstance(data, dict):
            if executable:  executable = (executable % data).lower()
            if title:       title = (title % data).lower()

        windows = Window.get_all_windows()
        for window in windows:
            if not window.is_visible:
                continue
            if (window.executable.endswith("natspeak.exe")
                and window.classname == "#32770"
                and window.get_position().dy < 50):
                # If a window matches the above, it is very probably
                #  the results-box of DNS.  We ignore this because
                #  its title is the words of the last recognition,
                #  which will often interfere with a search for
                #  a window with a spoken title.
                continue

            if executable:
                if window.executable.lower().find(executable) == -1:
                    continue
            if title:
                if window.title.lower().find(title) == -1:
                    continue
            window.set_foreground()
            return
        raise ActionError("Failed to find window (%s)."  % self._str)
