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

import sys
import os

# Windows
if sys.platform.startswith("win"):
    from .win32_monitor import Win32Monitor as Monitor

# Mac OS
elif sys.platform == "darwin":
    from .darwin_monitor import DarwinMonitor as Monitor

# Linux/X11
elif os.environ.get("XDG_SESSION_TYPE") == "x11":
    from .x11_monitor import X11Monitor as Monitor

# Unsupported
else:
    from .base_monitor import FakeMonitor as Monitor


class MonitorList(object):
    """
    Special read-only, self-updating monitors list class.

    Supports indexing and iteration.
    """

    def __init__(self):
        self._list = None  # lazily initialised

    def _update(self):
        self._list = Monitor.get_all_monitors()

    def __getitem__(self, index):
        self._update()
        return self._list[index]

    def __iter__(self):
        self._update()
        return iter(self._list)


#: :class:`MonitorsList` instance
monitors = MonitorList()
