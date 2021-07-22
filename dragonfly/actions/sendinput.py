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
Win32 input wrapper functions.

This file implements an interface to the Win32 SendInput function
for simulating keyboard and mouse events.
"""

# pylint: disable=E0401
# This file imports Win32-only symbols.

import sys
from ctypes import (c_short, c_long, c_ushort, c_ulong, sizeof,
                    POINTER, pointer, Structure, Union, windll)

import win32con
import win32api


class KeyboardInput(Structure):
    """Win32 KEYBDINPUT wrapper."""

    _fields_ = [("wVk", c_ushort),
                ("wScan", c_ushort),
                ("dwFlags", c_ulong),
                ("time", c_ulong),
                ("dwExtraInfo", POINTER(c_ulong))]

    #  From https://docs.microsoft.com/en-us/windows/desktop/inputdev/about-keyboard-input#extended-key-flag
    #     The extended keys consist of the ALT and CTRL keys
    #     on the right-hand side of the keyboard; the INS, DEL, HOME,
    #     END, PAGE UP, PAGE DOWN, and arrow keys in the clusters to
    #     the left of the numeric keypad; the NUM LOCK key; the BREAK
    #     (CTRL+PAUSE) key; the PRINT SCRN key; and the divide (/) and
    #     ENTER keys in the numeric keypad.
    #
    #  It's unclear if the Windows keys are also "extended", so they
    #  have been included for historical reasons.
    extended_keys = {
        win32con.VK_UP,
        win32con.VK_DOWN,
        win32con.VK_LEFT,
        win32con.VK_RIGHT,
        win32con.VK_HOME,
        win32con.VK_END,
        win32con.VK_PRIOR,
        win32con.VK_NEXT,
        win32con.VK_INSERT,
        win32con.VK_DELETE,
        win32con.VK_NUMLOCK,
        win32con.VK_RCONTROL,
        win32con.VK_RMENU,
        win32con.VK_PAUSE,
        win32con.VK_SNAPSHOT,
        win32con.VK_DIVIDE,
        win32con.VK_LWIN,
        win32con.VK_RWIN,
    }
    soft_keys = {
        win32con.VK_PAUSE,
    }


    def __init__(self, virtual_keycode, down, scancode=None, layout=None):
        """Initialize structure based on key type."""
        flags = 0
        if virtual_keycode == 0:
            flags |= 4  # KEYEVENTF_UNICODE
        else:
            # Translate *virtual_keycode* into a scan code, if necessary.
            #  Assume that *layout* is a keyboard layout (HKL).
            if scancode is None:
                user32 = windll.user32
                if sys.getwindowsversion().major < 6:
                    map_type = 0  # MAPVK_VK_TO_VSC
                else:
                    map_type = 4  # MAPVK_VK_TO_VSC_EX
                if layout is None:
                    scancode = user32.MapVirtualKeyW(virtual_keycode,
                                                     map_type)
                else:
                    scancode = user32.MapVirtualKeyExW(virtual_keycode,
                                                       map_type,
                                                       layout)

            # Add the KEYEVENTF_SCANCODE flag if the Win32 MapVirtualKey(Ex)
            #  function returned a translation.  If not, then fallback on
            #  the specified keycode.  This is also done for "soft" keys.
            if scancode and virtual_keycode not in self.soft_keys:
                flags |= 8  # KEYEVENTF_SCANCODE

                # Add the KEYEVENTF_EXTENDEDKEY flag, if necessary.
                #  Starting with Windows Vista, extended scan codes are
                #  specified with the high byte containing either 0xe0 or
                #  0xe1.
                if scancode >> 8 in (0xe0, 0xe1):
                    flags |= win32con.KEYEVENTF_EXTENDEDKEY

            # Always add the KEYEVENTF_EXTENDEDKEY flag for certain
            #  virtual-keys (see above).
            if virtual_keycode in self.extended_keys:
                flags |= win32con.KEYEVENTF_EXTENDEDKEY

        if not down:
            flags |= win32con.KEYEVENTF_KEYUP

        extra = pointer(c_ulong(0))
        Structure.__init__(self, virtual_keycode, scancode, flags, 0, extra)


class HardwareInput(Structure):
    _fields_ = [("uMsg", c_ulong),
                ("wParamL", c_short),
                ("wParamH", c_ushort)]

class MouseInput(Structure):
    _fields_ = [("dx", c_long),
                ("dy", c_long),
                ("mouseData", c_ulong),
                ("dwFlags", c_ulong),
                ("time",c_ulong),
                ("dwExtraInfo", POINTER(c_ulong))]


class _InputUnion(Union):
    _fields_ = [("ki", KeyboardInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class _Input(Structure):
    _fields_ = [("type", c_ulong),
                ("ii", _InputUnion)]

    def __init__(self, element):
        if   isinstance(element, KeyboardInput):
            element_type = win32con.INPUT_KEYBOARD
            union = _InputUnion(ki=element)
        elif isinstance(element, MouseInput):
            element_type = win32con.INPUT_MOUSE
            union = _InputUnion(mi=element)
        elif isinstance(element, HardwareInput):
            element_type = win32con.INPUT_HARDWARE
            union = _InputUnion(hi=element)
        else: raise TypeError("Unknown input type: %r" % element)

        Structure.__init__(self, type=element_type, ii=union)


def make_input_array(inputs):
    arguments = [(i,) for i in inputs]
    InputArray = _Input * len(inputs)
    return InputArray(*arguments)


def send_input_array(input_array):
    length = len(input_array)
    assert length >= 0
    size = sizeof(input_array[0])
    ptr = pointer(input_array)

    count_inserted = windll.user32.SendInput(length, ptr, size)

    if count_inserted != length:
        last_error = win32api.GetLastError()
        message = win32api.FormatMessage(last_error)
        raise ValueError("windll.user32.SendInput(): %s" % (message))
