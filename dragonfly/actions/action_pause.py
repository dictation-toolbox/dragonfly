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
Pause action
============================================================================

"""


import time
from dragonfly.actions.action_base import DynStrActionBase


class Pause(DynStrActionBase):
    """
        Pause for the given amount of time.

        The *spec* constructor argument should be a *string* giving the
        time to wait.  It should be given in hundredths of a second.  For
        example, the following code will pause for 20/100s = 0.2
        seconds: ::

            Pause("20").execute()

        The reason the *spec* must be given as a *string* is because it
        can then be used in dynamic value evaluation.  For example, the
        following code determines the time to pause at execution time: ::

            action = Pause("%(time)d")
            data = {"time": 37}
            action.execute(data)

    """

    def _parse_spec(self, spec):
        interval = float(spec) / 100
        return interval

    # pylint: disable=W0221
    # Arguments differ from DynStrActionBase._execute_events().
    def _execute_events(self, interval):
        time.sleep(interval)
        return True
