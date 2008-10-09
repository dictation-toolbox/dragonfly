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
    This file implements a Point class for geometry operations.
"""


#===========================================================================

class Point(object):

    #-----------------------------------------------------------------------
    # Methods for initialization, copying, and introspection.

    def __init__(self, x=None, y=None):
        self._x = 0.0; self._y = 0.0
        if x != None: self.x = x
        if y != None: self.y = y

    def copy(self):     return Point(x=self._x, y=self._y)
    def __copy__(self): return self.copy()

    def __str__(self):
        return "%s(%.2f,%.2f)" % (self.__class__.__name__, self._x, self._y)

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    def _set_x(self, x):
        if isinstance(x, float):    self._x = x
        elif isinstance(x, int):    self._x = float(x)
        else: raise TypeError("Point coordinate must be an int or float;"
                              " received %r." % x)
    x = property(fget=lambda self: self._x,
                 fset=_set_x,
                 doc="Protected access to x attribute.")

    def _set_y(self, y):
        if isinstance(y, float):    self._y = y
        elif isinstance(y, int):    self._y = float(y)
        else: raise TypeError("Point coordinate must be an int or float;"
                              " received %r." % y)
    y = property(fget=lambda self: self._y,
                 fset=_set_y,
                 doc="Protected access to y attribute.")

    #-----------------------------------------------------------------------
    # Methods for manipulating point objects.

    def __iadd__(self, other):
        """Translate point by adding another point's coordinates."""
        if not isinstance(other, Point): return NotImplemented
        self._x += other._x
        self._y += other._y
        return self

    def __add__(self, other):
        """Create a new point with coordinates of this point and other
            added up."""
        if not isinstance(other, Point): return NotImplemented
        clone = self.copy()
        clone += other
        return clone

    def translate(self, dx, dy):
        """camp point."""
        other = Point(dx, dy)
        self += other

    def interpolate(self, other, fraction):
        """Create a new point with coordinates interpolated between
            this point and another."""
        if not isinstance(other, Point):
            raise TypeError("Can only interpolate between points;"
                            " received %r" % other)
        x1 = self._x; y1 = self._y; x2 = other._x; y2 = other._y
        x3 = x1 + (x2 - x1) * fraction
        y3 = y1 + (y2 - y1) * fraction
        return Point(x3, y3)

    def average(self, other):
        """Translate point."""
        return self.interpolate(other, 0.5)

    def renormalize(self, src, dst):
#       assert isinstance(src, Rectangle)
#       assert isinstance(dst, Rectangle)
        nx = (self._x - src.x1) / src.dx
        self._x = dst.x1 + nx * dst.dx
        ny = (self._y - src.y1) / src.dy
        self._y = dst.y1 + ny * dst.dy
        return self
