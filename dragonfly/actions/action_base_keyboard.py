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

# pylint: disable=W0603
# Suppress warnings about global statements used for configuration.

# pylint: disable=E1111
# Implementations of BaseKeyboardAction return different types for events.

import os

from dragonfly.actions.action_base import DynStrActionBase
from dragonfly.actions.keyboard    import Keyboard
from dragonfly.actions.typeables   import typeables


class BaseKeyboardAction(DynStrActionBase):
    """
        Base keystroke emulation action.

    """

    _keyboard = Keyboard()

    def __init__(self, spec=None, static=False, use_hardware=False):
        self._use_hardware = use_hardware
        super(BaseKeyboardAction, self).__init__(spec, static)

    def require_hardware_events(self):
        """
        Return `True` if the current context requires hardware emulation.
        """
        if self._use_hardware: return True

        # If this is a Windows system, delegate to the keyboard class.
        # Otherwise, return false.
        if os.name == "nt": return self._keyboard.require_hardware_events()
        else: return False

    def _get_typeable(self, key_symbol, use_hardware):
        # Use the Typeable object for the symbol, if it exists.
        typeable = typeables.get(key_symbol)
        if typeable:
            # Update the object and return it.
            typeable.update(use_hardware)
            return typeable

        # Otherwise, get a new Typeable for the symbol, if possible.
        is_text = not use_hardware
        try:
            typeable = self._keyboard.get_typeable(key_symbol,
                                                   is_text=is_text)
        except ValueError:
            pass

        # If getting a Typeable failed, then, if it is allowed, try
        #  again with is_text=True.  On Windows, this will use Unicode
        #  events instead.
        if not (typeable or use_hardware):
            try:
                typeable = self._keyboard.get_typeable(key_symbol,
                                                       is_text=True)
            except ValueError:
                pass

        return typeable
