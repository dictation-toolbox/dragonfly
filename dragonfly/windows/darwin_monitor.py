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

from AppKit import NSScreen

from .base_monitor import BaseMonitor
from .rectangle import Rectangle


#---------------------------------------------------------------------------
# List of monitors that will be filled when this module is loaded and
# updated on calls to `Monitor.update_monitors_list`.

monitors = []


#===========================================================================
# Monitor class for storing info about single display monitor.

class DarwinMonitor(BaseMonitor):
    """
    The monitor class used on Mac OS (Darwin).

    Monitors for Mac OS are **not** automatically updated because ``AppKit``
    doesn't update monitor information after it is retrieved. A simple
    workaround for this is to restart the Python interpreter after a monitor
    change.

    """

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    @classmethod
    def update_monitors_list(cls):
        # Get a list of the current monitor handles.
        monitor_handles = [m.handle for m in monitors]

        # Get monitor information from AppKit.
        new_monitor_handles = []
        for screen in NSScreen.screens():
            handle = screen.deviceDescription()['NSScreenNumber']
            frame = screen.frame()
            dx = frame.size.width - frame.origin.x
            dy = frame.size.height - frame.origin.y
            rectangle = Rectangle(frame.origin.x, frame.origin.y, dx, dy)

            # Check if this monitor is already in the list.
            if handle in monitor_handles:
                # Replace the monitor's rectangle if it has changed.
                index = monitor_handles.index(handle)
                monitor = monitors[index]
                if rectangle != monitor._rectangle:
                    monitor.rectangle = rectangle
            else:
                # Add a new monitor object to the list.
                monitors.append(cls(handle, rectangle))

            # Keep track of each monitor handle.
            new_monitor_handles.append(handle)

        # Remove any monitors whose handles weren't found.
        for monitor in tuple(monitors):
            if monitor.handle not in new_monitor_handles:
                monitors.remove(monitor)


# Enumerate monitors and build Dragonfly's monitor list when this
# module is loaded.
DarwinMonitor.update_monitors_list()
