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
import dragonfly.windows.rectangle as rectangle_


#===========================================================================

class Monitor(object):

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, handle, rectangle):
        assert isinstance(handle, int)
        self._handle = handle
        assert isinstance(rectangle, rectangle_.Rectangle)
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
        assert isinstance(rectangle, rectangle_.Rectangle)
        self._rectangle = rectangle # Should make a copy??
    rectangle = property(fget=lambda self: self._rectangle,
                      fset=_set_rectangle,
                      doc="Protected access to rectangle attribute.")


#===========================================================================

monitors = [
    Monitor(0, rectangle_.Rectangle(   0, 0, 1920, 1200)),
    Monitor(0, rectangle_.Rectangle(1920, 0, 1600, 1200)),
    ]


# Public Const SM_XVIRTUALSCREEN = 76    'virtual desktop left
# Public Const SM_YVIRTUALSCREEN = 77    'virtual top
# Public Const SM_CXVIRTUALSCREEN = 78   'virtual width
# Public Const SM_CYVIRTUALSCREEN = 79   'virtual height
# Public Const SM_CMONITORS = 80         'number of monitors
# Public Const SM_SAMEDISPLAYFORMAT = 81
# numMonitors = GetSystemMetrics(SM_CMONITORS)
# GetSystemMetrics(SM_XVIRTUALSCREEN)
# GetSystemMetrics(SM_YVIRTUALSCREEN)
# GetSystemMetrics(SM_CYVIRTUALSCREEN)
# GetSystemMetrics(SM_CXVIRTUALSCREEN)
