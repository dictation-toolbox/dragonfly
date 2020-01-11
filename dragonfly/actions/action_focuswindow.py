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
FocusWindow action
============================================================================

"""

from .action_base      import ActionBase, ActionError
from ..windows  import Window


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
         - *index* (*str* or *int*) -- zero-based index of the target
           window, for multiple matching windows; can be a string (for
           substitution) but must be convertible to an integer.
         - *filter_func* (*callable*) -- called with a single argument
           (the window object), and should return ``True`` for your
           target windows; example:
           ``lambda window: window.get_position().dy > 100``.
         - *focus_only* (*bool*, default *False*) -- if *True*, then
           attempt to focus the window without raising it by using the
           *Window.set_focus()* method instead of *set_foreground()*.
           This argument may do nothing depending on the platform.

        This action searches all visible windows for a window which
        matches the given parameters.

    """

    def __init__(self, executable=None, title=None, index=None,
                 filter_func=None, focus_only=False):
        if executable:  self.executable = executable.lower()
        else:           self.executable = None
        if title:       self.title = title.lower()
        else:           self.title = None
        self.index = index
        self.filter_func = filter_func
        self.focus_only = focus_only
        ActionBase.__init__(self)

        arguments = []
        if executable:  arguments.append("executable=%r" % executable)
        if title:       arguments.append("title=%r" % title)
        if index:       arguments.append("index=%r" % index)
        if filter_func: arguments.append("filter_func=%r" % filter_func)
        if focus_only:  arguments.append("focus_only=%r" % focus_only)
        self._str = ", ".join(arguments)

    def _execute(self, data=None):
        executable = self.executable
        title = self.title
        index = self.index
        if data and isinstance(data, dict):
            if executable:  executable = (executable % data).lower()
            if title:       title = (title % data).lower()
            if index:       index = (index % data).lower()

        index = int(index) if index else 0

        # Get the first matching window and bring it to the foreground.
        windows = Window.get_matching_windows(executable, title)
        if self.filter_func:
            windows = [window for window in windows
                       if self.filter_func(window)]
        if windows and (index < len(windows)):
            window = windows[index]
            if self.focus_only:
                window.set_focus()
            else:
                window.set_foreground()
        else:
            raise ActionError("Failed to find window (%s)." % self._str)
