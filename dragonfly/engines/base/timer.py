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

from threading import Thread

#---------------------------------------------------------------------------

class Timer(object):
    """
    Timer class for calling a function every N seconds.

    Constructor arguments:

     - *function* (*callable*) -- the function to call every N seconds. Must
       have no required arguments.
     - *interval* (*float*) -- number of seconds between calls to the
       function.
     - *manager* (:class:`TimerManagerBase`) -- engine timer manager instance.

    Instances of this class are normally initialised from
    :meth:`engine.create_timer`.
    """

    _log = logging.getLogger("engine.timer")

    def __init__(self, function, interval, manager):
        self.function = function
        self.interval = interval
        self.manager = manager
        self.active = False
        self.next_time = None
        self.start()

    def start(self):
        """
        Start calling the timer's function on an interval.

        This method is called on initialisation.
        """
        if self.active:
            return
        self.manager.add_timer(self)
        self.active = True
        self.next_time = time.time() + self.interval

    def stop(self):
        """ Stop calling the timer's function on an interval. """
        if not self.active:
            return
        self.manager.remove_timer(self)
        self.active = False
        self.next_time = None

    def call(self):
        """
        Call the timer's function.

        This method is normally called by the timer manager.
        """
        self.next_time += self.interval
        try:
            self.function()
        except Exception as e:
            self._log.exception("Exception during timer callback: %s" % (e,))


class TimerManagerBase(object):
    """ Base timer manager class. """

    _log = logging.getLogger("engine.timer")

    def __init__(self, interval, engine):
        self.interval = interval
        self.engine = engine
        self.timers = []

    def add_timer(self, timer):
        """ Add a timer and activate the main callback if required. """
        self.timers.append(timer)
        if len(self.timers) == 1:
            self._activate_main_callback(self.main_callback,
                                         self.interval)

    def remove_timer(self, timer):
        """ Remove a timer and deactivate the main callback if required. """
        try:
            self.timers.remove(timer)
        except Exception as e:
            self._log.exception("Failed to remove timer: %s" % e)
            return
        if len(self.timers) == 0:
            self._deactivate_main_callback()

    def main_callback(self):
        """ Method to call each timer's function when required. """
        now = time.time()
        for c in self.timers:
            if c.next_time < now:
                try:
                    c.call()
                except Exception as e:
                    self._log.exception("Exception occurred during"
                                        " timer callback: %s" % (e,))

    def _activate_main_callback(self, callback, msec):
        """
        Virtual method to implement to start calling :meth:`main_callback`
        on an interval.
        """
        raise NotImplementedError("_activate_main_callback() not implemented for"
                                  " %s class." % self.__class__.__name__)

    def _deactivate_main_callback(self):
        """
        Virtual method to implement to stop calling :meth:`main_callback` on
        an interval.
        """
        raise NotImplementedError("_deactivate_main_callback() not implemented for"
                                  " %s class." % self.__class__.__name__)


class ThreadedTimerManager(TimerManagerBase):
    """
    Timer manager class using a daemon thread.

    This class is used by the "text" engine.

    It may be used by any SR engine that supports engine operations on
    multiple threads.
    """

    def __init__(self, interval, engine):
        TimerManagerBase.__init__(self, interval, engine)
        self._running = False
        self._thread = None

    def _activate_main_callback(self, callback, sec):
        """"""
        # Do nothing if the thread is already running.
        if self._running:
            return

        def run():
            while self._running:
                time.sleep(sec)
                callback()

        self._running = True
        self._thread = Thread(target=run)
        self._thread.setDaemon(True)
        self._thread.start()

    def _deactivate_main_callback(self):
        """"""
        # Stop the thread's main loop and wait until it finishes, timing out
        # after 5 seconds.
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None


class DelegateTimerManagerInterface(object):
    """
    DelegateTimerManager interface.
    """
    def set_timer_callback(self, callback, sec):
        """
        Virtual method to set the timer manager's callback.

        :param callback: function to call every N seconds
        :type callback: callable | None
        :param sec: number of seconds between calls to the callback function
        :type sec: float | int
        """
        raise NotImplementedError()


class DelegateTimerManager(TimerManagerBase):
    """
    Timer manager class that calls :meth:`main_callback` through an
    engine-specific callback function.

    Engines using this class must implement
    :class:`DelegateManagerInterface`.

    This class is used by the SAPI 5 engine.
    """

    def __init__(self, interval, engine):
        TimerManagerBase.__init__(self, interval, engine)
        if not isinstance(self.engine, DelegateTimerManagerInterface):
            raise TypeError("engines using ProxyTimerManager must "
                            "implement ProxyManagerInterface")

    def _activate_main_callback(self, callback, sec):
        """"""
        self.engine.set_timer_callback(callback, sec)

    def _deactivate_main_callback(self):
        """"""
        self.engine.set_timer_callback(None, 0)
