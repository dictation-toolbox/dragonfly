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
    This file offers an interface to the system's information about
    available monitors (a.k.a. screens, displays).
"""

import logging

from six import integer_types

from .rectangle import Rectangle


#---------------------------------------------------------------------------
# List of monitors that will be filled when this module is loaded and
# updated on calls to `Monitor.update_monitors_list`.

monitors = []


#===========================================================================
# Monitor classes for storing info about single display monitor.

class BaseMonitor(object):

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

    @classmethod
    def update_monitors_list(cls):
        """
        Update dragonfly's monitors list with new monitors, delete monitors
        that aren't found and replace rectangles of monitors that have
        changed.
        """
        pass

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    def _set_handle(self, handle):
        assert isinstance(handle, integer_types)
        self._handle = handle

    handle = property(fget=lambda self: self._handle,
                      fset=_set_handle,
                      doc="Protected access to handle attribute.")

    def _get_updated_rectangle(self):
        self.update_monitors_list()
        return self._rectangle

    def _set_rectangle(self, rectangle):
        assert isinstance(rectangle, Rectangle)
        self._rectangle = rectangle  # Should make a copy??

    rectangle = property(fget=_get_updated_rectangle,
                         fset=_set_rectangle,
                         doc="Protected access to rectangle attribute.")


# Enumerate monitors and build Dragonfly's monitor list when this
# module is loaded.
BaseMonitor.update_monitors_list()
