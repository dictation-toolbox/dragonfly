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
    This file offers an interface to the Win32 information about
    available monitors (a.k.a. screens, displays).
"""
from six import integer_types

import win32api
import logging

from .rectangle import Rectangle


#---------------------------------------------------------------------------
# List of monitors that will be filled when this module is loaded and
# updated on calls to `Monitor.update_monitors_list`.

monitors = []


#===========================================================================
# Monitor class for storing info about single display monitor.

class Monitor(object):

    _log = logging.getLogger("monitor.init")

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, handle, rectangle):
        assert isinstance(handle, integer_types)
        self._handle = handle
        assert isinstance(rectangle, Rectangle)
        self._rectangle = rectangle

    def __str__(self):
        return "%s(%d)" % (self.__class__.__name__, self._handle)

    @staticmethod
    def update_monitors_list():
        """
        Update dragonfly's monitors list with new monitors, delete monitors
        that aren't found and replace rectangles of monitors that have
        changed.
        """
        # Get an updated list of monitor information and the handles of
        # monitors in the list at the moment.
        updated_monitors = win32api.EnumDisplayMonitors()
        monitor_handles = [m.handle for m in monitors]

        # Update the list with any new or changed monitors.
        for h1, _, rectangle in updated_monitors:
            handle = h1.handle
            x1, x2, dx, dy = rectangle

            # Check if the monitors list already contains this monitor.
            if handle in monitor_handles:
                # Replace the rectangle for the monitor if it has changed.
                i = monitor_handles.index(handle)
                m = monitors[i]
                r = Rectangle(x1, x2, dx, dy)
                if r != m._rectangle:
                    Monitor._log.debug("Setting %s.rectangle to %s"
                                       % (m, r))
                    m.rectangle = r
            else:
                # Add the new monitor to the list.
                m = Monitor(handle, Rectangle(x1, x2, dx, dy))
                Monitor._log.debug("Adding %s to monitors list" % m)
                monitors.append(m)

        # Remove any monitors that aren't in the updated list.
        monitor_handles = [h1.handle for h1, _, _ in updated_monitors]
        for m in list(monitors):
            if m.handle not in monitor_handles:
                Monitor._log.debug("Removing %s from monitors list" % m)
                monitors.remove(m)

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    def _set_handle(self, handle):
        assert isinstance(handle, integer_types)
        self._handle = handle
    handle = property(fget=lambda self: self._handle,
                      fset=_set_handle,
                      doc="Protected access to handle attribute.")

    def _get_updated_rectangle(self):
        Monitor.update_monitors_list()
        return self._rectangle

    def _set_rectangle(self, rectangle):
        assert isinstance(rectangle, Rectangle)
        self._rectangle = rectangle  # Should make a copy??
    rectangle = property(fget=_get_updated_rectangle,
                         fset=_set_rectangle,
                         doc="Protected access to rectangle attribute.")


# Enumerate monitors and build Dragonfly's monitor list when this
# module is loaded.
Monitor.update_monitors_list()
