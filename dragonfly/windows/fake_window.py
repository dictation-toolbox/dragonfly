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

# pylint: disable=W0622
# Suppress warnings about redefining the built-in 'id' function.

from .base_window import BaseWindow
from .rectangle import Rectangle


class FakeWindow(BaseWindow):
    """ Fake Window class used when no implementation is available. """

    fake_title = ''
    fake_classname = ''
    fake_executable = ''
    fake_pid = 0

    @classmethod
    def get_foreground(cls):
        return FakeWindow(id=0)

    def __init__(self, id):
        super(FakeWindow, self).__init__(id)
        self._rectangle = Rectangle()

    @classmethod
    def get_all_windows(cls):
        return []

    #-----------------------------------------------------------------------
    # Methods and properties for window attributes.

    def _get_window_text(self):
        return self.fake_title

    def _get_class_name(self):
        return self.fake_classname

    def _get_window_module(self):
        return self.fake_executable

    def _get_window_pid(self):
        return self.fake_pid

    @property
    def is_minimized(self):
        return False

    @property
    def is_maximized(self):
        return False

    @property
    def is_visible(self):
        return True

    #-----------------------------------------------------------------------
    # Methods related to window geometry.

    def get_position(self):
        return self._rectangle

    def set_position(self, rectangle):
        assert isinstance(rectangle, Rectangle)
        self._rectangle = rectangle

    #-----------------------------------------------------------------------
    # Methods for miscellaneous window control.

    def minimize(self):
        pass

    def maximize(self):
        pass

    def restore(self):
        pass

    def close(self):
        pass

    def set_foreground(self):
        pass

    def set_focus(self):
        pass
