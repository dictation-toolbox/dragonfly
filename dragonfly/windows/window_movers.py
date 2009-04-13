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
Window mover classes
============================================================================

"""

from math          import sqrt
from .rectangle    import Rectangle, unit
from ..timer       import timer


#===========================================================================

class PathBase(object):

    _interval = 0.025

    def __init__(self, window, origin, destination, speed=1.0):
        self._window = window
        self._origin = origin
        self._destination = destination
        self._speed = speed
        self._fractions = self._calc_fraction_list()

    def start(self):
        timer.add_callback(self.timer_callback, self._interval)

    def stop(self):
        timer.remove_callback(self.timer_callback)

    def timer_callback(self):
        if not self._fractions:
            self.stop()
            self._window.set_position(self._destination)
            return
        fraction = self._fractions.pop(0)
        rectangle = self._calc_rect_from_fraction(fraction)
        self._window.set_position(rectangle)


class LinearPath(PathBase):

    _step_size = 30

    def _calc_fraction_list(self):
        step_size = float(self._step_size) * self._speed
        oc = self._origin.center
        dc = self._destination.center
        dx = oc.x - dc.x
        dy = oc.y - dc.y
        distance = sqrt(dx**2 + dy**2)
        print "distance", distance
        print "step size", step_size
        print "fraction size", step_size/distance
        step_fraction = step_size / distance
        return [(i * step_fraction) for i in range(0, int(distance / step_size))]

    def _calc_rect_from_fraction(self, fraction):
        p1 = self._origin.p1.interpolate(self._destination.p1, fraction)
        p2 = self._origin.p2.interpolate(self._destination.p2, fraction)
        rectangle = Rectangle(p1.x, p1.y, p2.x - p1.x, p2.y - p1.y)
        return rectangle


#===========================================================================

class WindowMover(object):

    def __init__(self, path_type):
        self._path_type = path_type

    def move_window(self, window, origin, destination):
        path = self._path_type(window, origin, destination)
        path.start()


#===========================================================================

window_movers = {
                 "linear": WindowMover(LinearPath),
                }
