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
Multiplexing interface to a timer
============================================================================

"""

import time
import logging


#---------------------------------------------------------------------------

class Timer(object):

    _log = logging.getLogger("engine.timer")

    def __init__(self, function, interval, manager):
        self.function = function
        self.interval = interval
        self.manager = manager
        self.active = False
        self.next_time = None
        self.start()

    def start(self):
        if self.active:
            return
        self.manager.add_timer(self)
        self.active = True
        self.next_time = time.clock() + self.interval

    def stop(self):
        if not self.active:
            return
        self.manager.remove_timer(self)
        self.active = False
        self.next_time = None

    def call(self):
        self.next_time += self.interval
        try:
            self.function()
        except Exception as e:
            self._log.exception("Exception during timer callback: %s" % (e,))


class TimerManagerBase(object):
    """
    """

    _log = logging.getLogger("engine.timer")

    def __init__(self, interval, engine):
        """
        """
        self.interval = interval
        self.engine = engine
        self.timers = []

    def add_timer(self, timer):
        self.timers.append(timer)
        if len(self.timers) == 1:
            self._activate_main_callback(self.main_callback,
                                         self.interval)

    def remove_timer(self, timer):
        try:
            self.timers.remove(timer)
        except Exception as e:
            self._log.exception("Failed to remove timer: %s" % e)
            return
        if len(self.timers) == 0:
            self._deactivate_main_callback()

    def main_callback(self):
        now = time.clock()
        for c in self.timers:
            if c.next_time < now:
                try:
                    c.call()
                except Exception as e:
                    self._log.exception("Exception occurred during"
                                        " timer callback: %s" % (e,))

    def _activate_main_callback(self, callback, msec):
        raise NotImplementedError("_activate_main_callback() not implemented for"
                                  " %s class." % self.__class__.__name__)

    def _deactivate_main_callback(self):
        raise NotImplementedError("_deactivate_main_callback() not implemented for"
                                  " %s class." % self.__class__.__name__)
