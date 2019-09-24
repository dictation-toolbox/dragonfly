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
    This file offers an interface to X11 information about
    available monitors (a.k.a. screens, displays).
"""

from six import integer_types, string_types

from .base_monitor import BaseMonitor
from .rectangle import Rectangle


#---------------------------------------------------------------------------
# List of monitors that will be filled when this module is loaded and
# updated on calls to `Monitor.update_monitors_list`.

monitors = []


#===========================================================================
# Monitor class for storing info about single display monitor.

class X11Monitor(BaseMonitor):

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, name, rectangle):
        assert isinstance(name, string_types)
        self._name = name

        # Get a numeric value from the name that we can use as a handle.
        handle = hash(name)
        super(X11Monitor, self).__init__(handle, rectangle)

    def __str__(self):
        return "%s(%d)" % (self.__class__.__name__, self._name)

    @classmethod
    def update_monitors_list(cls):
        pass

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    def _set_name(self, name):
        assert isinstance(name, string_types)
        self._name = name

        # Also set the handle, as it is derived from the name.
        self._set_handle(hash(name))

    name = property(fget=lambda self: self._name,
                      fset=_set_name,
                      doc="Protected access to name attribute.")


# Enumerate monitors and build Dragonfly's monitor list when this
# module is loaded.
X11Monitor.update_monitors_list()
