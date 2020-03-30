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

import logging

from six import integer_types

from .rectangle import Rectangle


#===========================================================================
# Monitor classes for storing info about a single display monitor.

class BaseMonitor(object):
    """
    The base monitor class.
    """

    _log = logging.getLogger("monitor.init")

    #-----------------------------------------------------------------------
    # Class attributes to retrieve existing Monitor objects.

    _monitors_by_handle = {}

    #-----------------------------------------------------------------------
    # Class methods to create new Monitor objects.

    @classmethod
    def get_monitor(cls, handle, rectangle):
        """
        Get a :class:`Monitor` object given a monitor handle.

        Given the same handle, this method will return the same object.

        :param handle: monitor handle
        :type handle: int
        :param rectangle: monitor rectangle
        :type rectangle: Rectangle
        :rtype: Monitor
        :returns: monitor
        """
        if handle in cls._monitors_by_handle:
            monitor = cls._monitors_by_handle[handle]
            monitor.rectangle = rectangle
        else:
            monitor = cls(handle, rectangle)
            cls._monitors_by_handle[handle] = monitor
        return monitor

    @classmethod
    def get_all_monitors(cls):
        """
        Get a list containing each connected monitor.

        :rtype: list
        :returns: monitors
        """
        raise NotImplementedError()

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, handle, rectangle):
        assert isinstance(handle, integer_types)
        self._handle = handle
        assert isinstance(rectangle, Rectangle)
        self._rectangle = rectangle

    def __repr__(self):
        return "%s(%d)" % (self.__class__.__name__, self._handle)

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    def _set_handle(self, handle):
        assert isinstance(handle, integer_types)
        self._handle = handle

    handle = property(fget=lambda self: self._handle,
                      fset=_set_handle,
                      doc="Protected access to handle attribute.")

    def _set_rectangle(self, rectangle):
        assert isinstance(rectangle, Rectangle)
        self._rectangle = rectangle  # Should make a copy??

    rectangle = property(fget=lambda self: self._rectangle,
                         fset=_set_rectangle,
                         doc="Protected access to rectangle attribute.")

    @property
    def is_primary(self):
        """
        Whether this is the primary display monitor.

        :rtype: bool
        :returns: true or false
        """
        rect = self.rectangle
        return rect.x == 0 and rect.y == 0

    @property
    def name(self):
        """
        The name of this monitor.

        :rtype: str
        :returns: monitor name
        """
        raise NotImplementedError()


class FakeMonitor(BaseMonitor):
    """
    The monitor class used on unsupported platforms.
    """

    @classmethod
    def get_all_monitors(cls):
        return []

    @property
    def name(self):
        """
        The name of this monitor.

        :rtype: str
        :returns: monitor name
        """
        return self.__class__.__name__
