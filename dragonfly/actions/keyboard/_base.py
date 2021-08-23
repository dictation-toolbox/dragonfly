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

""" This file defines the base keyboard interface classes. """

import logging


class BaseKeySymbols(object):
    pass


class MockKeySymbols(BaseKeySymbols):
    def __getattribute__(self, _):
        # No keys can be typed, so return -1.
        return -1


class BaseKeyboard(object):
    """ Base keyboard interface. """

    _log = logging.getLogger("keyboard")

    @classmethod
    def send_keyboard_events(cls, events):
        """ Send a sequence of keyboard events. """
        # TODO Add a URL to the docs?
        raise NotImplementedError("Keyboard support is not implemented for "
                                  "this platform or your platform was not "
                                  "detected correctly.  Please see the "
                                  "documentation.")

    @classmethod
    def get_typeable(cls, char, is_text=False):
        """ Get a Typeable object. """
        return BaseTypeable(cls, char)


class BaseTypeable(object):
    """Container for keypress events."""

    __slots__ = ("_code", "_modifiers", "_name", "_is_text")

    _log = logging.getLogger("keyboard")

    def __init__(self, code, modifiers=(), name=None, is_text=False):
        """Set keypress information."""
        self._code = code
        self._modifiers = modifiers
        self._name = name
        self._is_text = is_text

    # pylint: disable=no-self-use,unused-argument
    def update(self, hardware_events_required):
        """
        Update keypress information.

        :rtype: bool
        :returns: success
        """
        return True

    def __repr__(self):
        """ Return information useful for debugging. """
        return ("%s(%s)" % (self.__class__.__name__, self._name) +
                repr(self.events()))

    def on_events(self, timeout=0):
        """Return events for pressing this key down."""
        events = [(m, True, 0) for m in self._modifiers]
        events.append((self._code, True, timeout))
        return events

    def off_events(self, timeout=0):
        """Return events for releasing this key."""
        events = [(m, False, 0) for m in self._modifiers]
        events.append((self._code, False, timeout))
        events.reverse()
        return events

    def events(self, timeout=0):
        """Return events for pressing and then releasing this key."""
        events = [(self._code, True, 0), (self._code, False, timeout)]
        for m in self._modifiers[-1::-1]:
            events.insert(0, (m, True, 0))
            events.append((m, False, 0))
        return events
