#
# This file is part of Dragonfly.
# (c) Copyright 2021 by Ryan Hileman
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
Timer manager class for the Talon Engine
============================================================================

"""

from dragonfly.engines.base import TimerManagerBase

from talon import cron
from threading import RLock


class TalonTimerManager(TimerManagerBase):
    """ Talon timer manager class. """

    def __init__(self, interval, engine):
        self.interval = interval
        self.engine = engine
        self.timers = {}
        self._lock = RLock()

    def add_timer(self, timer):
        """Add a timer."""
        spec = cron.seconds_to_timespec(timer.interval)
        if timer.repeating:
            job = cron.interval(spec, timer.call)
        else:
            job = cron.after(spec, timer.call)
        with self._lock:
            cron.cancel(self.timers.get(timer))
            self.timers[timer] = job

    def remove_timer(self, timer):
        """Remove a timer."""
        with self._lock:
            job = self.timers.pop(timer, None)
            cron.cancel(job)

    def enable(self):
        """
        Method to re-enable the main timer callback.
        This does nothing in Talon.
        """

    def disable(self):
        """
        Method to disable execution of the main timer callback.
        This does nothing in Talon.
        """

    def main_callback(self):
        """
        Method to call each timer's function when required.
        This does nothing in Talon.
        """
