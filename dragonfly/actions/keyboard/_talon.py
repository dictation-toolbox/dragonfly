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
This file implements a keyboard interface using Talon.
"""

import logging
import sys
import time

from ._base import BaseKeyboard, Typeable as BaseTypeable
from talon import ctrl

class Typeable(BaseTypeable):
    """ Typeable class for talon. """
    _log = logging.getLogger("keyboard")

    def __init__(self, code, modifiers=(), name=None, is_text=False):
        BaseTypeable.__init__(self, code, modifiers, name, is_text)


class TalonKeySymbols(object):
    """ Key symbols for Talon. """

    # Whitespace and editing keys
    RETURN = 'enter'
    TAB = 'tab'
    SPACE = 'space'
    BACK = 'backspace'
    DELETE = 'delete'

    # Main modifier keys
    SHIFT = 'shift'
    CONTROL = 'ctrl'
    ALT = 'alt'

    # Right modifier keys
    RSHIFT = 'rshift'
    RCONTROL = 'rctrl'
    RALT = 'ralt'

    # Special keys
    ESCAPE = 'escape'
    INSERT = 'insert'
    PAUSE = 'pause'
    LSUPER = 'super'
    RSUPER = 'rsuper'
    APPS = 'menu'
    SNAPSHOT = 'printscr'

    # Lock keys
    SCROLL_LOCK = 'scroll_lock'
    NUM_LOCK = 'numlock'
    CAPS_LOCK = 'capslock'

    # Navigation keys
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'
    PAGE_UP = 'pageup'
    PAGE_DOWN = 'pagedown'
    HOME = 'home'
    END = 'end'

    # Number pad keys
    MULTIPLY = 'keypad_multiply'
    ADD = 'keypad_add'
    SEPARATOR = 'keypad_decimal'
    SUBTRACT = 'keypad_minus'
    DECIMAL = 'keypad_decimal'
    DIVIDE = 'keypad_divide'
    NUMPAD0 = 'keypad_0'
    NUMPAD1 = 'keypad_1'
    NUMPAD2 = 'keypad_2'
    NUMPAD3 = 'keypad_3'
    NUMPAD4 = 'keypad_4'
    NUMPAD5 = 'keypad_5'
    NUMPAD6 = 'keypad_6'
    NUMPAD7 = 'keypad_7'
    NUMPAD8 = 'keypad_8'
    NUMPAD9 = 'keypad_9'

    # Function keys
    F1 = 'f1'
    F2 = 'f2'
    F3 = 'f3'
    F4 = 'f4'
    F5 = 'f5'
    F6 = 'f6'
    F7 = 'f7'
    F8 = 'f8'
    F9 = 'f9'
    F10 = 'f10'
    F11 = 'f11'
    F12 = 'f12'
    F13 = 'f13'
    F14 = 'f14'
    F15 = 'f15'
    F16 = 'f16'
    F17 = 'f17'
    F18 = 'f18'
    F19 = 'f19'
    F20 = 'f20'
    F21 = 'f21'
    F22 = 'f22'
    F23 = 'f23'
    F24 = 'f24'

    # Multimedia keys
    VOLUME_UP = 'volup'
    VOLUME_DOWN = 'voldown'
    VOLUME_MUTE = 'mute'
    MEDIA_NEXT_TRACK = 'next'
    MEDIA_PREV_TRACK = 'prev'
    MEDIA_PLAY_PAUSE = 'play_pause'
    BROWSER_BACK = 'page_back'
    BROWSER_FORWARD = 'page_next'


class Keyboard(BaseKeyboard):
    """Static class wrapper around talon.ctrl."""

    _log = logging.getLogger("keyboard")

    @classmethod
    def send_keyboard_events(cls, events):
        """
        Send a sequence of keyboard events.

        Positional arguments:
        events -- a sequence of tuples of the form
            (name, down, timeout), where
                name (str): Talon key name.
                down (boolean): True means the key will be pressed down,
                    False means the key will be released.
                timeout (int): number of seconds to sleep after
                    the keyboard event.

        """
        cls._log.debug("Keyboard.send_keyboard_events %r", events)
        for event in events:
            (key, down, timeout) = event

            # Press/release the key, catching any errors.
            try:
                ctrl.key_press(key, down=down)
            except Exception as e:
                cls._log.exception("Failed to type key code %s: %s",
                                   key, e)

            # Sleep after the keyboard event if necessary.
            if timeout:
                time.sleep(timeout)

    @classmethod
    def get_typeable(cls, char, is_text=False):
        return Typeable(char, is_text=is_text)
