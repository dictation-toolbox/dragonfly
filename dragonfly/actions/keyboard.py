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
This file implements a Win32 keyboard interface using sendinput.

"""


import time
import win32con
from ctypes import windll, c_char, c_wchar
from dragonfly.actions.sendinput import (KeyboardInput, make_input_array,
                                         send_input_array)


#---------------------------------------------------------------------------
# Typeable class.

class Typeable(object):

    __slots__ = ("_code", "_modifiers", "_name")

    def __init__(self, code, modifiers=(), name=None):
        self._code = code
        self._modifiers = modifiers
        self._name = name

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._name) + repr(self.events())

    def on_events(self, timeout=0):
        events = [(m, True, 0) for m in self._modifiers]
        events.append((self._code, True, timeout))
        return events

    def off_events(self, timeout=0):
        events = [(m, False, 0) for m in self._modifiers]
        events.append((self._code, False, timeout))
        events.reverse()
        return events

    def events(self, timeout=0):
        events = [(self._code, True, 0), (self._code, False, timeout)]
        for m in self._modifiers[-1::-1]:
            events.insert(0, (m, True, 0))
            events.append((m, False , 0))
        return events


#---------------------------------------------------------------------------
# Keyboard access class.

class Keyboard(object):

    shift_code =    win32con.VK_SHIFT
    ctrl_code =     win32con.VK_CONTROL
    alt_code =      win32con.VK_MENU

    @classmethod
    def send_keyboard_events(cls, events):
        """
            Send a sequence of keyboard events.

            Positional arguments:
            events -- a sequence of 3-tuples of the form
                (keycode, down, timeout), where
                keycode (int): virtual key code.
                down (boolean): True means the key will be pressed down,
                    False means the key will be released.
                timeout (int): number of seconds to sleep after
                    the keyboard event.

        """
        items = []
        for keycode, down, timeout in events:
            input = KeyboardInput(keycode, down)
            items.append(input)
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
    def xget_virtual_keycode(cls, char):
        if isinstance(char, str):
            code = windll.user32.VkKeyScanA(c_char(char))
        else:
            code = windll.user32.VkKeyScanW(c_wchar(char))
        if code == -1:
            raise ValueError("Unknown char: %r" % char)

        # Construct a list of the virtual key code and modifiers.
        codes = [code & 0x00ff]
        if   code & 0x0100: codes.append(cls.shift_code)
        elif code & 0x0200: codes.append(cls.ctrl_code)
        elif code & 0x0400: codes.append(cls.alt_code)
        return codes

    @classmethod
    def get_keycode_and_modifiers(cls, char):
        if isinstance(char, str):
            code = windll.user32.VkKeyScanA(c_char(char))
        else:
            code = windll.user32.VkKeyScanW(c_wchar(char))
        if code == -1:
            raise ValueError("Unknown char: %r" % char)

        # Construct a list of the virtual key code and modifiers.
        modifiers = []
        if   code & 0x0100: modifiers.append(cls.shift_code)
        elif code & 0x0200: modifiers.append(cls.ctrl_code)
        elif code & 0x0400: modifiers.append(cls.alt_code)
        code &= 0x00ff
        return code, modifiers

    @classmethod
    def get_typeable(cls, char):
        code, modifiers = cls.get_keycode_and_modifiers(char)
        return Typeable(code, modifiers)


keyboard = Keyboard()
