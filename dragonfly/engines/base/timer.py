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

from threading import Thread, current_thread, RLock

#---------------------------------------------------------------------------

class Timer(object):
    """
    Timer class for calling a function every N seconds.

    Constructor arguments:

     - *function* (*callable*) -- the function to call every N seconds. Must
       have no required arguments.
     - *interval* (*float*) -- number of seconds between calls to the
       function. Note that this is on a best-effort basis only.
     - *manager* (:class:`TimerManagerBase`) -- engine timer manager instance.
     - *repeating* (*bool*) -- whether to call the function every N seconds
       or just once (default: True).

    Instances of this class are normally initialised from
    :meth:`engine.create_timer`.
    """

    _log = logging.getLogger("engine.timer")

    def __init__(self, function, interval, manager, repeating=True):
        self.function = function
        self.interval = interval
        self.manager = manager
        self.repeating = repeating
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
        self.next_time = time.time() + self.interval
        try:
            self.function()
        except Exception as e:
            self._log.exception("Exception during timer callback: %s" % (e,))
        if not self.repeating:
            self.stop()


class TimerManagerBase(object):
    """ Base timer manager class. """

    _log = logging.getLogger("engine.timer")

    def __init__(self, interval, engine):
        self.interval = interval
        self.engine = engine
        self.timers = []
        self._lock = RLock()
        self._enabled = True
        self._active = False

    def add_timer(self, timer):
        """ Add a timer and activate the main callback if required. """
        with self._lock:
            self.timers.append(timer)
        if len(self.timers) == 1 and self._enabled:
            self._activate_main_callback(self.main_callback,
                                         self.interval)
            self._active = True

    def remove_timer(self, timer):
        """ Remove a timer and deactivate the main callback if required. """
        try:
            with self._lock:
                self.timers.remove(timer)
        except Exception as e:
            self._log.exception("Failed to remove timer: %s" % e)
            return
        if len(self.timers) == 0 and self._enabled:
            self._deactivate_main_callback()
            self._active = False

    def enable(self):
        """
        Method to re-enable the main timer callback.

        The main timer callback is enabled by default. This method is only
        useful if :meth:`disable` is called.
        """
        self._enabled = True

    def disable(self):
        """
        Method to disable execution of the main timer callback.

        This method is used for testing timer-related functionality without
        race conditions.
        """
        self._enabled = False

    def main_callback(self):
        """ Method to call each timer's function when required. """
        # Deactivate the engine's main callback if necessary. We don't
        # return early here because this method should work if called
        # manually.
        if not self._enabled and self._active:
            self._deactivate_main_callback()
            self._active = False

        now = time.time()
        for c in tuple(self.timers):
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

    This class is used by the "text" engine. It is only suitable for engine
    backends with no recognition loop to execute timer functions on.

    .. warning::

       The timer interface is **not** thread-safe. Use the :meth:`enable`
       and :meth:`disable` methods if you need finer control over timer
       function execution.
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
        should_join = (self._thread and self._thread.is_alive() and
                       self._thread is not current_thread())
        self._running = False
        if should_join:
            timeout = 5
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                raise RuntimeError("failed to deactivate main callback "
                                   "after %d seconds" % timeout)


class DelegateTimerManagerInterface(object):
    """
    DelegateTimerManager interface.
    """

    def __init__(self):
        self._timer_callback = None
        self._timer_interval = None
        self._timer_next_time = 0

    def set_timer_callback(self, callback, sec):
        """
        Method to set the timer manager's callback.

        :param callback: function to call every N seconds
        :type callback: callable | None
        :param sec: number of seconds between calls to the callback function
        :type sec: float | int
        """
        self._timer_callback = callback
        self._timer_interval = sec
        self._timer_next_time = time.time()

    def call_timer_callback(self):
        """"""
        if not (self._timer_callback and self._timer_interval):
            return

        now = time.time()
        if self._timer_next_time < now:
            self._timer_next_time = now + self._timer_interval
            self._timer_callback()


class DelegateTimerManager(TimerManagerBase):
    """
    Timer manager class that calls :meth:`main_callback` through an
    engine-specific callback function.

    Engines using this class should implement the methods in
    :class:`DelegateManagerInterface`.

    This class is used by the SAPI 5 engine.
    """

    def __init__(self, interval, engine):
        TimerManagerBase.__init__(self, interval, engine)

    def _activate_main_callback(self, callback, sec):
        """"""
        self.engine.set_timer_callback(callback, sec)

    def _deactivate_main_callback(self):
        """"""
        self.engine.set_timer_callback(None, 0)
