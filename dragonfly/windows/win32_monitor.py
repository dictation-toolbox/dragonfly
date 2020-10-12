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
# This file imports a Win32-only module.

import ctypes
import logging

import win32api

from .base_monitor import BaseMonitor
from .rectangle import Rectangle

# Force the current process to be DPI aware. This will ensure that the
# resolution is reported properly even when DPI scaling is on. This appears to
# be set to PROCESS_SYSTEM_DPI_AWARE when running embedded in Dragon, which
# provides awareness of the DPI when the application starts, but not when it
# changes. Unfortunately, this cannot be changed (presumably it is declared in a
# manifest). When running from the command line, however, the default is
# PROCESS_DPI_UNAWARE and can be adjusted here.
try:
    log = logging.getLogger("monitor.init")
    value = 2  # PROCESS_PER_MONITOR_DPI_AWARE
    hresult = ctypes.windll.shcore.SetProcessDpiAwareness(value)
    if hresult == -2147024809:  # E_INVALIDARG
        log.warning("DPI awareness could not be set; "
                    "SetProcessDpiAwareness() received an invalid "
                    "argument: %d", value)
    elif hresult == -2147024891:  # E_ACCESSDENIED
        log.warning("DPI awareness could not be set; it has been set "
                    "already.")
except OSError:
    # Do nothing if SetProcessDpiAwareness() could not be called.
    pass


#===========================================================================
# Monitor class for storing info about a single display monitor.

class Win32Monitor(BaseMonitor):
    """
    The monitor class used on Win32.
    """

    #-----------------------------------------------------------------------
    # Class methods to create new Monitor objects.

    @classmethod
    def get_all_monitors(cls):
        # Get an updated list of monitors.
        monitors = []
        for py_handle, _, rectangle in win32api.EnumDisplayMonitors():
            # Get the monitor handle.
            handle = py_handle.handle

            # Create a rectangle object representing the monitor's
            # dimensions and relative position.
            top_left_x, top_left_y, bottom_right_x, bottom_right_y = rectangle
            dx = bottom_right_x - top_left_x
            dy = bottom_right_y - top_left_y
            rectangle = Rectangle(top_left_x, top_left_y, dx, dy)

            # Get a new or updated monitor object and add it to the list.
            # Ensure that the primary monitor is first on the list.
            monitor = cls.get_monitor(handle, rectangle)
            if monitor.is_primary:
                monitors.insert(0, monitor)
            else:
                monitors.append(monitor)

        return monitors

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    @property
    def is_primary(self):
        """
        Whether this is the primary display monitor.

        :rtype: bool
        :returns: true or false
        """
        monitor_info = win32api.GetMonitorInfo(self._handle)
        return monitor_info["Flags"] & 1 == 1

    @property
    def name(self):
        """
        The device name of this monitor.

        :rtype: str
        :returns: monitor name
        """
        monitor_info = win32api.GetMonitorInfo(self._handle)
        return monitor_info["Device"]
