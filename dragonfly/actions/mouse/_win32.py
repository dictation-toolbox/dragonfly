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

# pylint: disable=E0401
# This file imports Win32-only symbols.

from ctypes import windll, pointer, c_long, c_ulong, Structure

import win32con

from dragonfly.actions.sendinput import (MouseInput, make_input_array,
                                         send_input_array)
from ._base import BaseButtonEvent, MoveEvent


#---------------------------------------------------------------------------
# Functions and event delegate for getting and setting the cursor position.

class Point(Structure):
    _fields_ = [
        ('x',  c_long),
        ('y',  c_long),
    ]


def get_cursor_position():
    point = Point()
    result = windll.user32.GetCursorPos(pointer(point))
    if result:
        return point.x, point.y
    else:
        return None


def set_cursor_position(x, y):
    result = windll.user32.SetCursorPos(c_long(int(x)), c_long(int(y)))
    return not result


class MoveEventDelegate(object):

    @classmethod
    def get_position(cls):
        return get_cursor_position()

    @classmethod
    def set_position(cls, x, y):
        return set_cursor_position(x, y)


# Set MoveEvent's delegate. This allows us to set platform-specific
# functions for getting and setting the cursor position without having
# to do a lot of sub-classing for no good reason.
MoveEvent.delegate = MoveEventDelegate()

#---------------------------------------------------------------------------
# Win32 mouse button and wheel up/down flags.

# Taken from https://msdn.microsoft.com/en-us/library/windows/desktop/ms646273(v=vs.85).aspx
MOUSEEVENTF_HWHEEL = 0x1000

PLATFORM_BUTTON_FLAGS = {
    "left":   ((win32con.MOUSEEVENTF_LEFTDOWN, 0),
               (win32con.MOUSEEVENTF_LEFTUP, 0)),
    "right":  ((win32con.MOUSEEVENTF_RIGHTDOWN, 0),
               (win32con.MOUSEEVENTF_RIGHTUP, 0)),
    "middle": ((win32con.MOUSEEVENTF_MIDDLEDOWN, 0),
               (win32con.MOUSEEVENTF_MIDDLEUP, 0)),
    "four": ((win32con.MOUSEEVENTF_XDOWN, 1),
             (win32con.MOUSEEVENTF_XUP, 1)),
    "five": ((win32con.MOUSEEVENTF_XDOWN, 2),
             (win32con.MOUSEEVENTF_XUP, 2)),
}

PLATFORM_WHEEL_FLAGS = {
    "wheelup": (win32con.MOUSEEVENTF_WHEEL, 120),
    "stepup": (win32con.MOUSEEVENTF_WHEEL, 40),
    "wheeldown": (win32con.MOUSEEVENTF_WHEEL, -120),
    "stepdown": (win32con.MOUSEEVENTF_WHEEL, -40),
    "wheelright": (MOUSEEVENTF_HWHEEL, 120),
    "stepright": (MOUSEEVENTF_HWHEEL, 40),
    "wheelleft": (MOUSEEVENTF_HWHEEL, -120),
    "stepleft": (MOUSEEVENTF_HWHEEL, -40),
}


#---------------------------------------------------------------------------
# Win32 event classes.

class ButtonEvent(BaseButtonEvent):

    def execute(self, window):
        # Ensure that the primary mouse button is the *left* button before
        #  sending events.
        primary_changed = windll.user32.SwapMouseButton(0)
        try:
            # Prepare and send the mouse events.
            zero = pointer(c_ulong(0))
            inputs = [MouseInput(0, 0, flag[1], flag[0], 0, zero)
                      for flag in self._flags]
            array = make_input_array(inputs)
            send_input_array(array)
        finally:
            # Swap the primary mouse button back if it was previously set
            #  to *right*.
            if primary_changed:
                windll.user32.SwapMouseButton(1)
