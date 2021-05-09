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

import math
import random
import threading
import time

from .point        import Point
from .rectangle    import Rectangle, unit


#===========================================================================

def linear_fraction_generator():
    def _linear_fraction_generator(count):
        step = float(1) / count
        for index in range(count):
            yield step * index
    return _linear_fraction_generator

def sine_fraction_generator(begin=-0.5, end=0.5):
    begin_radians = -begin * math.pi
    end_radians   = -end   * math.pi
    def _sine_fraction_generator(count):
        step = (end_radians - begin_radians) / count

        sample_points = [(step*i - begin_radians) for i in range(count)]
        fractions = [math.sin(x) for x in sample_points]
        minimum = min(fractions)
        maximum = max(fractions)
        for f in fractions:
            yield (f - minimum) / (maximum - minimum)
    return _sine_fraction_generator


#---------------------------------------------------------------------------

def linear_path():
    def _linear_path(p1, p2, fractions):
        for fraction in fractions:
            p = p1.interpolate(p2, fraction)
            yield p
    return _linear_path

def spline_path():
    distance_min = 0.5
    distance_max = 1.0
    offset_max = 0.7

    def _spline_path(p1, p2, fractions):
        distance_factor = random.uniform(distance_min, distance_max)
        offset_factor = random.uniform(-offset_max, offset_max)
        delta = p2 - p1
        base = p1.interpolate(p2, distance_factor)
        spline_x = base.x + delta.y * offset_factor
        spline_y = base.y - delta.x * offset_factor
        pm = Point(spline_x, spline_y)

        for fraction in fractions:
            p1m = p1.interpolate(pm, fraction)
            pm2 = pm.interpolate(p2, fraction)
            p = p1m.interpolate(pm2, fraction)
            yield p

    return _spline_path

def linear_resize_path(max_count=10):
    def _linear_resize_path(r1, r2, count):
        if count > max_count:  step = 1.0 / max_count
        else:                  step = 1.0 / count
        for index in range(count):
            if index >= max_count:
                yield r2.dx, r2.dy
            else:
                fraction = step * index
                dx = r1.dx + (r2.dx - r1.dx) * fraction
                dy = r1.dy + (r2.dy - r1.dy) * fraction
                yield dx, dy
    return _linear_resize_path


#===========================================================================

# pylint: disable=R0902,R0913
# Suppress warnings about too many instance attributes and constructor
# arguments.

class TimerThread(threading.Thread):
    def __init__(self, timer_callback, interval):
        threading.Thread.__init__(self)
        self._event = threading.Event()
        self._interval = interval
        self._timer_callback = timer_callback

    def stop(self):
        self._event.set()

    def run(self):
        while not self._event.is_set():
            time.sleep(self._interval)
            self._timer_callback()


class PathBase(object):

    _interval = 0.025

    def __init__(self, window, origin, destination, fraction_generator,
                 position_generator, size_generator, speed=1.0):
        self._window = window
        self._origin = origin
        self._destination = destination
        self._speed = speed
        self._fraction_generator = fraction_generator
        self._position_generator = position_generator
        self._size_generator     = size_generator

        distance = (destination.center - origin.center).magnitude
        count = int(distance / 40 / speed)
        if count < 10:
            count = 10
        self._rectangles = self._rectangle_generator(origin, destination, count)

        self._timer = None

    def start(self):
        if self._timer:
            return

        self._timer = TimerThread(self.timer_callback, self._interval)
        self._timer.start()

    def stop(self):
        if not self._timer:
            return

        self._timer.stop()
        self._timer = None
        self._rectangles = None

    def timer_callback(self):
        if not self._rectangles:
            self.stop()
            self._window.set_position(self._destination)
            return
        try:
            rectangle = next(self._rectangles)
        except StopIteration:
            self._rectangles = None
            self.stop()
            rectangle = self._destination
        self._window.set_position(rectangle)

    def _rectangle_generator(self, r1, r2, count):
        fractions = self._fraction_generator(count)
        positions = self._position_generator(r1.center, r2.center, fractions)
        sizes     = self._size_generator(r1, r2, count)
        for position, size in zip(positions, sizes):
            dx, dy = size
            x = position.x - dx/2
            y = position.y - dy/2
            yield Rectangle(x, y, dx, dy)


#===========================================================================

class WindowMover(object):

    def __init__(self, fraction_generator, position_generator,
                 size_generator, speed=1.0):
        self._fraction_generator = fraction_generator
        self._position_generator = position_generator
        self._size_generator     = size_generator
        self._speed = speed

    def move_window(self, window, origin, destination):
        path = PathBase(window, origin, destination,
                        self._fraction_generator, self._position_generator,
                        self._size_generator)
        path.start()


#===========================================================================

window_movers = {
    "spline":   WindowMover(
        sine_fraction_generator(),
        spline_path(),
        linear_resize_path(20),
    ),
    "linear":   WindowMover(
        linear_fraction_generator(),
        linear_path(),
        linear_resize_path(20),
    ),
}
