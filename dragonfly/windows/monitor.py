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


import win32gui
import ctypes

from ..log       import get_log
from .rectangle  import Rectangle


#---------------------------------------------------------------------------
# List of monitors that will be filled when this module is loaded.

monitors = []


#===========================================================================
# Monitor class for storing info about single display monitor.

class Monitor(object):

    _log = get_log("monitor.init")

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, handle, rectangle):
        assert isinstance(handle, int)
        self._handle = handle
        assert isinstance(rectangle, Rectangle)
        self._rectangle = rectangle

    def __str__(self):
        return "%s(%d)" % (self.__class__.__name__, self._handle)

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    def _set_handle(self, handle):
        assert isinstance(handle, int)
        self._handle = handle
    handle = property(fget=lambda self: self._handle,
                      fset=_set_handle,
                      doc="Protected access to handle attribute.")

    def _set_rectangle(self, rectangle):
        assert isinstance(rectangle, Rectangle)
        self._rectangle = rectangle # Should make a copy??
    rectangle = property(fget=lambda self: self._rectangle,
                      fset=_set_rectangle,
                      doc="Protected access to rectangle attribute.")


#===========================================================================
# Monitor info retrieval below lightly inspired by the following recipe:
#  http://code.activestate.com/recipes/460509/ by Martin Dengler (2005)
#  More info available here:
#  http://msdn.microsoft.com/en-us/library/ms534809.aspx

class _rect_t(ctypes.Structure):
    _fields_ = [
                ('left',    ctypes.c_long),
                ('top',     ctypes.c_long),
                ('right',   ctypes.c_long),
                ('bottom',  ctypes.c_long)
               ]

class _monitor_info_t(ctypes.Structure):
    _fields_ = [
                ('cbSize',     ctypes.c_ulong),
                ('rcMonitor',  _rect_t),
                ('rcWork',     _rect_t),
                ('dwFlags',    ctypes.c_ulong)
               ]

callback_t = ctypes.WINFUNCTYPE(
                                ctypes.c_int,
                                ctypes.c_ulong,
                                ctypes.c_ulong,
                                ctypes.POINTER(_rect_t),
                                ctypes.c_double
                               )

def _callback(
              hMonitor,     # Handle to display monitor
              hdcMonitor,   # Handle to monitor DC
              lprcMonitor,  # Intersection rectangle of monitor
              dwData        # Data
             ):
    # Retrieves monitor info.
    info = _monitor_info_t()
    info.cbSize     = ctypes.sizeof(_monitor_info_t)
    info.rcMonitor  = _rect_t()
    info.rcWork     = _rect_t()
    res = ctypes.windll.user32.GetMonitorInfoA(hMonitor, ctypes.byref(info))

    # Store monitor info.
    handle = int(hMonitor)
    r = info.rcWork
    rectangle = Rectangle(r.left, r.top, r.right - r.left, r.bottom - r.top)
    monitor = Monitor(handle, rectangle)
    Monitor._log.debug("Found monitor %s with geometry %s."
                       % (monitor, rectangle))
    monitors.append(monitor)

    # Continue enumerating monitors.
    return True


# Enumerate monitors and build Dragonfly's monitor list when this
#  module is loaded.
res = ctypes.windll.user32.EnumDisplayMonitors(0, 0, callback_t(_callback), 0)
