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
This file implements the Key action.
"""


from dragonfly.actions.actionbase import DynStrActionBase, ActionError
from dragonfly.actions.typeables import typeables
from dragonfly.actions.keyboard import Keyboard


#---------------------------------------------------------------------------

class Text(DynStrActionBase):

    _pause_default = 0.02
    _keyboard = Keyboard()
    _specials = {
                 "\n":   typeables["enter"],
                 "\t":   typeables["tab"],
                }

    def __init__(self, spec=None, static=False, pause=_pause_default):
        self._pause = pause
        DynStrActionBase.__init__(self, spec=spec, static=static)

    def _parse_spec(self, spec):
        events = []
        for character in spec:
            if character in self._specials:
                typeable = self._specials[character]
            else:
                typeable = Keyboard.get_typeable(character)
            events.extend(typeable.events(self._pause))
        return events

    def _execute_events(self, events):
        self._keyboard.send_keyboard_events(events)
        return True
