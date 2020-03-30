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

# pylint: disable=E0401
# This file imports MacOS-only symbols.

from AppKit import NSScreen

from .base_monitor import BaseMonitor
from .rectangle import Rectangle


#===========================================================================
# Monitor class for storing info about a single display monitor.

class DarwinMonitor(BaseMonitor):
    """
    The monitor class used on Mac OS (Darwin).

    Monitors for Mac OS are **not** automatically updated because ``AppKit``
    doesn't update monitor information after it is retrieved. A simple
    workaround for this is to restart the Python interpreter after a monitor
    change.

    """

    #-----------------------------------------------------------------------
    # Class methods to create new Monitor objects.

    @classmethod
    def get_all_monitors(cls):
        # Get monitor information from AppKit.
        monitors = []
        for screen in NSScreen.screens():
            # Get the monitor handle.
            handle = screen.deviceDescription()['NSScreenNumber']

            # Create a rectangle object representing the monitor's
            # dimensions and relative position.
            frame = screen.frame()
            dx = frame.size.width - frame.origin.x
            dy = frame.size.height - frame.origin.y
            rectangle = Rectangle(frame.origin.x, frame.origin.y, dx, dy)

            # Get a new or updated monitor object and add it to the list.
            monitors.append(cls.get_monitor(handle, rectangle))

        return monitors

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    @property
    def name(self):
        """ The name of this monitor. """
        handle = self.handle
        for screen in NSScreen.screens():
            if screen.deviceDescription()['NSScreenNumber'] == handle:
                return screen.localizedName()

        return u"macOS monitor"
