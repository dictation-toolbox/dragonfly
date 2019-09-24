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
    This file offers an interface to Win32 information about
    available monitors (a.k.a. screens, displays).
"""

import win32api

from .base_monitor import BaseMonitor
from .rectangle import Rectangle


#---------------------------------------------------------------------------
# List of monitors that will be filled when this module is loaded and
# updated on calls to `Monitor.update_monitors_list`.

monitors = []


#===========================================================================
# Monitor class for storing info about single display monitor.

class Win32Monitor(BaseMonitor):

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    @classmethod
    def update_monitors_list(cls):
        # Get an updated list of monitor information and the handles of
        # monitors in the list at the moment.
        updated_monitors = win32api.EnumDisplayMonitors()
        monitor_handles = [m.handle for m in monitors]

        # Update the list with any new or changed monitors.
        for h1, _, rectangle in updated_monitors:
            handle = h1.handle
            top_left_x, top_left_y, bottom_right_x, bottom_right_y = rectangle
            dx = bottom_right_x - top_left_x
            dy = bottom_right_y - top_left_y

            # Check if the monitors list already contains this monitor.
            if handle in monitor_handles:
                # Replace the rectangle for the monitor if it has changed.
                i = monitor_handles.index(handle)
                m = monitors[i]
                r = Rectangle(top_left_x, top_left_y, dx, dy)
                if r != m._rectangle:
                    cls._log.debug("Setting %s.rectangle to %s"
                                       % (m, r))
                    m.rectangle = r
            else:
                # Add the new monitor to the list.
                m = cls(handle, Rectangle(top_left_x, top_left_y, dx, dy))
                cls._log.debug("Adding %s to monitors list" % m)
                monitors.append(m)

        # Remove any monitors that aren't in the updated list.
        monitor_handles = [h1.handle for h1, _, _ in updated_monitors]
        for m in list(monitors):
            if m.handle not in monitor_handles:
                cls._log.debug("Removing %s from monitors list" % m)
                monitors.remove(m)

# Enumerate monitors and build Dragonfly's monitor list when this
# module is loaded. This should be done for concrete Monitor classes.
Win32Monitor.update_monitors_list()
