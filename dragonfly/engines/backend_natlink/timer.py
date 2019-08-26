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
Multiplexing interface to the Natlink timer
============================================================================

"""

from ..base import TimerManagerBase


#---------------------------------------------------------------------------

class NatlinkTimerManager(TimerManagerBase):
    """
    Timer manager for the Natlink engine.

    This class utilises :meth:`natlink.setTimerCallback` to ensure that
    timer functions are called on-time regardless of Dragon's current
    status.

    Python code run outside of timer functions will be blocked when
    ``natlink`` functions are executing. This is a
    `limitation with Python threads
    <https://docs.python.org/3/c-api/init.html#thread-state-and-the-global-interpreter-lock>`__.

    :meth:`engine.connect` must be called before using timers with this
    manager.

    **Note**: long-running timers will block dragonfly from processing
    what was said, so be careful with how you use them!
    """

    def __init__(self, interval, engine):
        """
        """
        TimerManagerBase.__init__(self, interval, engine)

    def _activate_main_callback(self, callback, sec):
        self.engine.natlink.setTimerCallback(callback, int(sec * 1000))

    def _deactivate_main_callback(self):
        self.engine.natlink.setTimerCallback(None, 0)
