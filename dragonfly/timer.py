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
    This file implements a basic multiplexing interface to the current
    engine's timer.
"""


import time
import logging

from dragonfly.engines import get_engine


class _Timer(object):
    """
    This class is **deprecated** and will be removed in a future release.

    Please use the :meth:`engine.create_timer` method instead.

    """

    _log = logging.getLogger("timer")

    class Callback(object):
        def __init__(self, function, interval):
            self.function = function
            self.interval = interval
            self.next_time = time.time() + self.interval
            self.timer = None

        def call(self):
            self.next_time += self.interval
            try:
                self.function()
            except Exception as e:
                _Timer._log.exception("Exception during timer callback")
                print("Exception during timer callback: %s (%r)" % (e, e))

    def __init__(self, interval):
        self.interval = interval
        self.callbacks = []
        self._log.warning("Dragonfly's _Timer class has been deprecated. "
                          "Please use engine.create_timer() instead.")

    def add_callback(self, function, interval):
        t = get_engine().create_timer(function, interval)
        c = self.Callback(function, interval)
        c.timer = t
        self.callbacks.append(c)

    def remove_callback(self, function):
        for c in self.callbacks:
            if c.function == function:
                self.callbacks.remove(c)
                c.timer.stop()

    def callback(self):
        now = time.time()
        for c in self.callbacks:
            if c.next_time < now:
                c.timer.call()


timer = _Timer(0.025)
