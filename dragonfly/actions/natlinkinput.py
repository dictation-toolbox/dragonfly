#
# This file is part of Dragonfly.
# (c) Copyright 2022 by Dane Finlay
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
Natlink input wrapper functions.

This file implements an interface to natlink's playEvents function
for simulating keyboard and mouse events via NatSpeak.
"""

import logging

import win32con

try:
    import natlink
except:
    natlink = None


_log = logging.getLogger("keyboard")

def send_input_array_natlink(input_array):
    # Check if Natlink can be used.
    if natlink is None or not natlink.isNatSpeakRunning(): return False

    # Take the same argument as the equivalent SendInput function.
    length = len(input_array)
    if length == 0: return True

    # Translate each input struct into a tuple that can be processed by
    #  NatSpeak.  Return False if any incompatible event is found.
    input_list = []
    for input in input_array:
        if input.type == win32con.INPUT_KEYBOARD:
            keybdinput = input.ii.ki
            keycode = keybdinput.wVk
            dwFlags = keybdinput.dwFlags
            if keycode == 0: return False  # Implies KEYEVENTF_UNICODE.
            msg = 0x101 if dwFlags & win32con.KEYEVENTF_KEYUP else 0x100
            event = (msg, keycode, 1)
        elif input.type == win32con.INPUT_MOUSE:
            mouseinput = input.ii.mi
            dwFlags = mouseinput.dwFlags
            if   dwFlags & win32con.MOUSEEVENTF_LEFTDOWN:   msg = 0x201
            elif dwFlags & win32con.MOUSEEVENTF_LEFTUP:     msg = 0x202
            elif dwFlags & win32con.MOUSEEVENTF_RIGHTDOWN:  msg = 0x204
            elif dwFlags & win32con.MOUSEEVENTF_RIGHTUP:    msg = 0x205
            elif dwFlags & win32con.MOUSEEVENTF_MIDDLEDOWN: msg = 0x207
            elif dwFlags & win32con.MOUSEEVENTF_MIDDLEUP:   msg = 0x208
            else: return False
            # Note: In Dragonfly the mouse is not moved via SendInput, so
            #  we just use the current cursor position.
            x, y = natlink.getCursorPos()
            event = (msg, x, y)
        else:
            return False
        input_list.append(event)

    # Attempt to send input via Natlink.
    retry = False
    try:
        natlink.playEvents(input_list)
    except natlink.NatError as err:
        # If this failed because we're not connected yet, attempt to
        #  connect to natlink and retry.
        if (str(err) == "Calling playEvents is not allowed before"
                        " calling natConnect"):
            natlink.natConnect()
            retry = True
        else:
            _log.exception("Exception sending input via Natlink: %s", err)
            return False

    # Retry, and disconnect afterward, if necessary.
    if retry:
        try:
            natlink.playEvents(input_list)
        except natlink.NatError as err:
            _log.exception("Exception sending input via Natlink: %s", err)
            return False
        finally:
            natlink.natDisconnect()
    return True
