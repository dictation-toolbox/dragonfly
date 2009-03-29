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
Playback action
============================================================================

"""

from time              import sleep
from .action_base      import ActionBase, ActionError
from ..engines.engine  import get_engine


#---------------------------------------------------------------------------

class Playback(ActionBase):
    """
        Playback a series of recognitions.

    """

    def __init__(self, series, speed=1):
        ActionBase.__init__(self)
        self._series = tuple(series)
        self._speed = float(speed)

    def _get_speed(self):
        return self._speed
    def _set_speed(self, speed):
        self._speed = float(speed)
    speed = property(fget=_get_speed, fset=_set_speed,
                     doc="Factor to speed up playback.")

    def _execute(self, data=None):
        engine = get_engine()

        # Mimic the series of recognitions.
        for words, interval in self._series:
            self._log.debug("Mimicking recognition: %r" % (words,))
            try:
                engine.mimic(words)
                if interval and self._speed:
                    sleep(interval / self._speed)
            except Exception, e:
                raise ActionError("Playback failed: %s" % e)
