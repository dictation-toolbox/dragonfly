# This file was part of Aenea
#
# Aenea is free software: you can redistribute it and/or modify it under
# the terms of version 3 of the GNU Lesser General Public License as
# published by the Free Software Foundation.
#
# Aenea is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with Aenea.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (2014) Alex Roper
# Alex Roper <alex@aroper.net>

# This keyboard implementation is based on Aenea's x11_libxdo.py file.

import logging
import os
import time

import xdo
import Xlib.display

from ._x11_base import BaseX11Keyboard, KEY_TRANSLATION


class LibxdoKeyboard(BaseX11Keyboard):
    """Static class for typing keys with python-libxdo."""

    _log = logging.getLogger("keyboard")
    display = Xlib.display.Display()
    libxdo = xdo.Xdo(os.environ.get('DISPLAY', ''))

    @classmethod
    def send_keyboard_events(cls, events):
        """
        Send a sequence of keyboard events.

        Positional arguments:
        events -- a sequence of tuples of the form
            (keycode, down, timeout), where
                keycode (str): key symbol.
                down (boolean): True means the key will be pressed down,
                    False means the key will be released.
                timeout (int): number of seconds to sleep after
                    the keyboard event.

        """
        cls._log.debug("Keyboard.send_keyboard_events %r", events)

        # TODO: We can distill this entire loop down to a single libxdo function
        # call when we figure out how to properly user charcode_t entities from
        # libxdo.
        for event in events:
            (key, down, timeout) = event
            delay_micros = int(timeout * 1000.0)
            key = KEY_TRANSLATION.get(key, key)

            # Press/release the key, catching any errors.
            try:
                if down:
                    cls.libxdo.send_keysequence_window_down(0, key, delay_micros)
                else:
                    cls.libxdo.send_keysequence_window_up(0, key, delay_micros)
            except Exception as e:
                cls._log.exception("Failed to type key code %s: %s",
                                   key, e)

            # Sleep after the keyboard event if necessary.
            if timeout:
                time.sleep(timeout)
