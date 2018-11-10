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

"""This file implements a Win32 keyboard interface using sendinput."""


import time
from six import text_type, PY2

import win32con

from ctypes import windll, c_char, c_wchar
from dragonfly.actions.sendinput import (KeyboardInput, make_input_array,
                                         send_input_array)


class Typeable(object):
    """Container for keypress events."""

    __slots__ = ("_code", "_modifiers", "_name", "_is_text")

    def __init__(self, code, modifiers=(), name=None, is_text=False):
        """Set keypress information."""
        self._code = code
        self._modifiers = modifiers
        self._name = name
        self._is_text = is_text

    def __str__(self):
        """Return information useful for debugging."""
        return ("%s(%s)" % (self.__class__.__name__, self._name) +
                repr(self.events()))

    def on_events(self, timeout=0):
        """Return events for pressing this key down."""
        if self._is_text:
            events = [(self._code, True, timeout, True)]
        else:
            events = [(m, True, 0) for m in self._modifiers]
            events.append((self._code, True, timeout))
        return events

    def off_events(self, timeout=0):
        """Return events for releasing this key."""
        if self._is_text:
            events = [(self._code, False, timeout, True)]
        else:
            events = [(m, False, 0) for m in self._modifiers]
            events.append((self._code, False, timeout))
            events.reverse()
        return events

    def events(self, timeout=0):
        """Return events for pressing and then releasing this key."""
        if self._is_text:
            events = [(self._code, True, timeout, True),
                      (self._code, False, timeout, True)]
        else:
            events = [(self._code, True, 0), (self._code, False, timeout)]
            for m in self._modifiers[-1::-1]:
                events.insert(0, (m, True, 0))
                events.append((m, False, 0))
        return events


class Keyboard(object):
    """Static class wrapper around SendInput."""

    shift_code = win32con.VK_SHIFT
    ctrl_code = win32con.VK_CONTROL
    alt_code = win32con.VK_MENU

    @classmethod
    def send_keyboard_events(cls, events):
        """
        Send a sequence of keyboard events.

        Positional arguments:
        events -- a sequence of tuples of the form
            (keycode, down, timeout), where
                keycode (int): Win32 Virtual Key code.
                down (boolean): True means the key will be pressed down,
                    False means the key will be released.
                timeout (int): number of seconds to sleep after
                    the keyboard event.
            or
            (character, down, timeout, is_text), where
                character (str): Unicode character.
                down (boolean): True means the key will be pressed down,
                    False means the key will be released.
                timeout (int): number of seconds to sleep after
                    the keyboard event.
                is_text (boolean): True means that the keypress is targeted
                    at a window or control that accepts Unicode text.
        """
        items = []
        for event in events:
            if len(event) == 3:
                keycode, down, timeout = event
                input_structure = KeyboardInput(keycode, down)
            elif len(event) == 4 and event[3]:
                character, down, timeout = event[:3]
                input_structure = KeyboardInput(0, down, scancode=character)
            items.append(input_structure)
            if timeout:
                array = make_input_array(items)
                items = []
                send_input_array(array)
                time.sleep(timeout)
        if items:
            array = make_input_array(items)
            send_input_array(array)
            if timeout: time.sleep(timeout)

    @classmethod
    def _get_initial_keycode(cls, char):
        layout = windll.user32.GetKeyboardLayout(0)
        if isinstance(char, str) and PY2:
            code = windll.user32.VkKeyScanExA(c_char(char), layout)
        elif isinstance(char, text_type):  # unicode for PY2, str for PY3
            code = windll.user32.VkKeyScanExW(c_wchar(char), layout)
        else:
            code = -1
        if code == -1:
            raise ValueError("Unknown char: %r" % char)
        return code

    @classmethod
    def xget_virtual_keycode(cls, char):
        code = cls._get_initial_keycode(char)

        # Construct a list of the virtual key code and modifiers.
        codes = [code & 0x00ff]
        if code & 0x0100: codes.append(cls.shift_code)
        if code & 0x0200: codes.append(cls.ctrl_code)
        if code & 0x0400: codes.append(cls.alt_code)
        return codes

    @classmethod
    def get_keycode_and_modifiers(cls, char):
        code = cls._get_initial_keycode(char)

        # Construct a list of the virtual key code and modifiers.
        modifiers = []
        if code & 0x0100: modifiers.append(cls.shift_code)
        if code & 0x0200: modifiers.append(cls.ctrl_code)
        if code & 0x0400: modifiers.append(cls.alt_code)
        code &= 0x00ff
        return code, modifiers

    @classmethod
    def get_typeable(cls, char, is_text=False):
        if is_text:
            return Typeable(char, is_text=True)
        code, modifiers = cls.get_keycode_and_modifiers(char)
        return Typeable(code, modifiers)


keyboard = Keyboard()
