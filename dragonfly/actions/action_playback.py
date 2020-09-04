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

The :class:`Playback` action mimics a sequence of recognitions.  This is
for example useful for repeating a series of prerecorded or predefined
voice-commands.

This class could for example be used to reload with one single action::

    action = Playback([
                       (["focus", "Natlink"], 1.0),
                       (["File"], 0.5),
                       (["Reload"], 0.0),
                     ])
    action.execute()


Mimic quirks
----------------------------------------------------------------------------

Some SR engine back-ends have confusing :meth:`engine.mimic` method
behavior.  See the engine-specific mimic method documentation in sections
under :ref:`RefEngines` for more information.


Class reference
----------------------------------------------------------------------------

"""

from time              import sleep
from .action_base      import ActionBase, ActionError
from ..engines         import get_engine


#---------------------------------------------------------------------------

class Playback(ActionBase):
    """ Playback a series of recognitions. """

    def __init__(self, series, speed=1):
        """
            Constructor arguments:
             - *series* (sequence of 2-tuples) --
               the recognitions to playback.  Each element must be a
               2-tuple of the form *(["words", "two", "mimic"], interval)*,
               where *interval* is a float giving the number of seconds to
               pause after the given words are mimicked.
             - *speed* (*float*) --
               the factor by which to speed up playback.  The intervals
               after each mimic are divided by this number.

        """
        ActionBase.__init__(self)
        self._series = tuple(series)
        self._speed = float(speed)
        self._str = str([w for w, i in self._series])

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
            self._log.debug("Mimicking recognition: %r", words)
            try:
                engine.mimic(words)
                if interval and self._speed:
                    sleep(interval / self._speed)
            except Exception as e:
                raise ActionError("Playback failed: %s" % e)
