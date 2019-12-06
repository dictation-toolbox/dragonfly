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
    This file implements a Rectangle class for geometric operations.
"""

import copy
from dragonfly.windows.point import Point


#===========================================================================
# Rectangle class.

class Rectangle(Point):

    #-----------------------------------------------------------------------
    # Methods for initialization, copying, and introspection.

    def __init__(self, x1=None, y1=None, dx=None, dy=None):
        Point.__init__(self, x1, y1)
        self._size = Point(dx, dy)

    def copy(self):
        return copy.deepcopy(self)
    def __copy__(self):
        return copy.deepcopy(self)

    def __repr__(self):
        return "%s(%.1f, %.1f, %.1f, %.1f)" \
            % (self.__class__.__name__, self.x, self.y, self.dx, self.dy)

    def __eq__(self, other):
        return (super(Rectangle, self).__eq__(other) and
                self.size == other.size)

    def __ne__(self, other):
        return not self.__eq__(other)

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    p1 = property(fget=lambda self: Point(self._x, self._y),
                  doc="Protected access to p1 attribute.")
    p2 = property(fget=lambda self: self.p1 + self._size,
                  doc="Protected access to p2 attribute.")
    size = property(fget=lambda self: self._size.copy() ,
                    doc="Protected access to size attribute.")

    x1 = Point.x
    y1 = Point.y

    def _set_x2(self, x):
        self._size.x = x    # Use type checking of Point class.
        self._size._x -= self._x
    x2 = property(fget=lambda self: self._x + self._size._x,
                  fset=_set_x2,
                  doc="Protected access to x2 attribute.")

    def _set_y2(self, y):
        self._size.y = y    # Use type checking of Point class.
        self._size._y -= self._y
    y2 = property(fget=lambda self: self._y + self._size._y,
                  fset=_set_y2,
                  doc="Protected access to y2 attribute.")

    def _get_center(self):
        return self.p1 + Point(self._size.x / 2, self._size.y / 2)
    center = property(fget=_get_center,
                      doc="Dynamic access to center attribute.")

    dx = property(fget=lambda self: self._size.x,
                  doc="Protected access to dx attribute.")
    dy = property(fget=lambda self: self._size.y,
                  doc="Protected access to dy attribute.")

    x_center = property(fget=lambda self: self.x + self._size.x / 2,
                        doc="Protected access to x_center attribute.")
    y_center = property(fget=lambda self: self.y + self._size.y / 2,
                        doc="Protected access to y_center attribute.")

    ltwh = property(fget=lambda self: (int(self._x), int(self._y),
                                       int(self._size._x),
                                       int(self._size._y)),
                    doc="Shortcut to left-top-with-height tuple.")

    #-----------------------------------------------------------------------
    # Methods for manipulating rectangle objects.

    def translate(self, dx, dy):
        other = Point(dx, dy)
        self += other

    def renormalize(self, src, dst):
        # pylint: disable=W0212
        # Suppress warnings about protected member access.
        p1 = self.p1.renormalize(src, dst)
        p2 = self.p2.renormalize(src, dst)
        self._x = p1.x
        self._y = p1.y
        self._size._x = p2.x - p1.x
        self._size._y = p2.y - p1.y

    #-----------------------------------------------------------------------
    # Methods for various rectangle related operations.

    def contains(self, p):
        """Test whether this rectangle instance contains a point."""
        assert isinstance(p, Point)
        return self.x1 <= p.x < self.x2 and self.y1 <= p.y < self.y2


#===========================================================================
# Unity rectangle instance.

unit = Rectangle(0.0, 0.0, 1.0, 1.0)
