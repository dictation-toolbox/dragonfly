#
# This file is part of Dragonfly.
# (c) Copyright 2018 by Dane Finlay
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
Multiplexing interface for the text input engine
=============================================================================

"""

import time

from threading import Thread

from ..base import TimerManagerBase


# ---------------------------------------------------------------------------


class TextTimerManager(TimerManagerBase):
    """
    Timer manager for the text input engine.
    """

    def __init__(self, interval, engine):
        TimerManagerBase.__init__(self, interval, engine)
        self._running = False
        self._thread = None

    def _activate_main_callback(self, callback, sec):
        # Do nothing if the thread is already running or if the engine is not
        # connected.
        if self._running or not self.engine.connected:
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
        self._running = False
        self._thread.join()
        self._thread = None
