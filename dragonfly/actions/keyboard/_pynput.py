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
This file implements the a keyboard interface using the *pynput* Python
package.

Currently, this interface can be used on macOS (Darwin) or X11.

"""

import time

from pynput.keyboard import Controller, KeyCode, Key

from ._base import BaseKeyboard, BaseTypeable, BaseKeySymbols


class PynputTypeable(BaseTypeable):
    """ Typeable class for pynput. """

    def __init__(self, code, modifiers=(), name=None, is_text=False):
        BaseTypeable.__init__(self, code, modifiers, name, is_text)


class SafeKeyCode(object):
    """
    Class to safely get key codes from pynput.
    """

    def __getattr__(self, name):
        # Get the key code from pynput, returning KeyCode(vk=-1, char=name)
        #  if the key name isn't present.  Keys are undefined on some
        #  platforms, e.g. "pause" on Darwin.
        return getattr(Key, name, KeyCode(vk=-1, char=name))


virtual_keys = SafeKeyCode()


class BasePynputKeySymbols(BaseKeySymbols):
    """ Base key symbols for pynput. """

    # Whitespace and editing keys
    RETURN = virtual_keys.enter
    TAB = virtual_keys.tab
    SPACE = virtual_keys.space
    BACK = virtual_keys.backspace
    DELETE = virtual_keys.delete

    # Main modifier keys
    SHIFT = virtual_keys.shift
    CONTROL = virtual_keys.ctrl
    ALT = virtual_keys.alt

    # Right modifier keys
    RSHIFT = virtual_keys.shift_r
    RCONTROL = virtual_keys.ctrl_r
    RALT = virtual_keys.alt_r

    # Special keys
    ESCAPE = virtual_keys.esc
    INSERT = virtual_keys.insert
    PAUSE = virtual_keys.pause
    LSUPER = virtual_keys.cmd_l
    RSUPER = virtual_keys.cmd_r
    APPS = virtual_keys.menu
    SNAPSHOT = virtual_keys.print_screen

    # Lock keys
    SCROLL_LOCK = virtual_keys.scroll_lock
    NUM_LOCK = virtual_keys.num_lock
    CAPS_LOCK = virtual_keys.caps_lock

    # Navigation keys
    UP = virtual_keys.up
    DOWN = virtual_keys.down
    LEFT = virtual_keys.left
    RIGHT = virtual_keys.right
    PAGE_UP = virtual_keys.page_up
    PAGE_DOWN = virtual_keys.page_down
    HOME = virtual_keys.home
    END = virtual_keys.end

    # Number pad keys
    # pynput currently only exposes these for Windows, so we'll map them to
    # equivalent characters and numbers instead.
    MULTIPLY = KeyCode(char="*")
    ADD = KeyCode(char="+")
    SEPARATOR = KeyCode(char=".")  # this is locale-dependent.
    SUBTRACT = KeyCode(char="-")
    DECIMAL = KeyCode(char=".")
    DIVIDE = KeyCode(char="/")
    NUMPAD0 = KeyCode(char="0")
    NUMPAD1 = KeyCode(char="1")
    NUMPAD2 = KeyCode(char="2")
    NUMPAD3 = KeyCode(char="3")
    NUMPAD4 = KeyCode(char="4")
    NUMPAD5 = KeyCode(char="5")
    NUMPAD6 = KeyCode(char="6")
    NUMPAD7 = KeyCode(char="7")
    NUMPAD8 = KeyCode(char="8")
    NUMPAD9 = KeyCode(char="9")

    # Function keys
    # F13-20 don't work on X11 with pynput because they are not usually
    # part of the keyboard map.
    F1 = virtual_keys.f1
    F2 = virtual_keys.f2
    F3 = virtual_keys.f3
    F4 = virtual_keys.f4
    F5 = virtual_keys.f5
    F6 = virtual_keys.f6
    F7 = virtual_keys.f7
    F8 = virtual_keys.f8
    F9 = virtual_keys.f9
    F10 = virtual_keys.f10
    F11 = virtual_keys.f11
    F12 = virtual_keys.f12
    F13 = virtual_keys.f13
    F14 = virtual_keys.f14
    F15 = virtual_keys.f15
    F16 = virtual_keys.f16
    F17 = virtual_keys.f17
    F18 = virtual_keys.f18
    F19 = virtual_keys.f19
    F20 = virtual_keys.f20


class X11KeySymbols(BasePynputKeySymbols):
    """
    Symbols for X11 from pynput.

    This class defines extra symbols matching those that dragonfly's Win32
    keyboard interface provides.
    """

    # Number pad keys
    # Retrieved from /usr/include/X11/keysymdef.h on Debian 9.
    MULTIPLY = KeyCode.from_vk(0xffaa)
    ADD = KeyCode.from_vk(0xffab)
    SEPARATOR = KeyCode.from_vk(0xffac)
    SUBTRACT = KeyCode.from_vk(0xffad)
    DECIMAL = KeyCode.from_vk(0xffae)
    DIVIDE = KeyCode.from_vk(0xffaf)
    NUMPAD0 = KeyCode.from_vk(0xffb0)
    NUMPAD1 = KeyCode.from_vk(0xffb1)
    NUMPAD2 = KeyCode.from_vk(0xffb2)
    NUMPAD3 = KeyCode.from_vk(0xffb3)
    NUMPAD4 = KeyCode.from_vk(0xffb4)
    NUMPAD5 = KeyCode.from_vk(0xffb5)
    NUMPAD6 = KeyCode.from_vk(0xffb6)
    NUMPAD7 = KeyCode.from_vk(0xffb7)
    NUMPAD8 = KeyCode.from_vk(0xffb8)
    NUMPAD9 = KeyCode.from_vk(0xffb9)

    # Function keys F21-F24.
    # Retrieved from /usr/include/X11/keysymdef.h on Debian 9.
    # These keys don't work on X11 with pynput because they are not usually
    # part of the keyboard map. They are set here to avoid some warnings
    # and because the Windows keyboard supports them.
    F21 = KeyCode.from_vk(0xffd1)
    F22 = KeyCode.from_vk(0xffd2)
    F23 = KeyCode.from_vk(0xffd3)
    F24 = KeyCode.from_vk(0xffd4)

    # Multimedia keys
    # Retrieved from /usr/include/X11/XF86keysym.h on Debian 9.
    # These should work on Debian-based distributions like Ubunutu, but
    # might not work using different X11 server implementations because the
    # symbols are vendor-specific.
    # Any errors raised when typing these or any other keys will be caught
    # and logged.
    VOLUME_UP = KeyCode.from_vk(0x1008FF13)
    VOLUME_DOWN = KeyCode.from_vk(0x1008FF11)
    VOLUME_MUTE = KeyCode.from_vk(0x1008FF12)
    MEDIA_NEXT_TRACK = KeyCode.from_vk(0x1008FF17)
    MEDIA_PREV_TRACK = KeyCode.from_vk(0x1008FF16)
    MEDIA_PLAY_PAUSE = KeyCode.from_vk(0x1008FF14)
    BROWSER_BACK = KeyCode.from_vk(0x1008FF26)
    BROWSER_FORWARD = KeyCode.from_vk(0x1008FF27)


class DarwinKeySymbols(BasePynputKeySymbols):
    """
    Symbols for Darwin from pynput.
    """

    # The key symbols below are defined solely to prevent errors in
    #  typeables.py.  ValueErrors will be raised by send_keyboard_events()
    #  if these symbols are given in an event sequence.

    # Extra function keys.
    F21 = virtual_keys.f21
    F22 = virtual_keys.f22
    F23 = virtual_keys.f23
    F24 = virtual_keys.f24

    # Multimedia keys.
    VOLUME_UP = virtual_keys.volume_up
    VOLUME_DOWN = virtual_keys.volume_down
    VOLUME_MUTE = virtual_keys.volume_mute
    MEDIA_NEXT_TRACK = virtual_keys.media_next_track
    MEDIA_PREV_TRACK = virtual_keys.media_prev_track
    MEDIA_PLAY_PAUSE = virtual_keys.media_play_pause
    BROWSER_BACK = virtual_keys.browser_back
    BROWSER_FORWARD = virtual_keys.browser_forward


class PynputKeyboard(BaseKeyboard):
    """Static class wrapper around pynput.keyboard."""

    _controller = Controller()

    @classmethod
    def send_keyboard_events(cls, events):
        """
        Send a sequence of keyboard events.

        Positional arguments:
        events -- a sequence of tuples of the form
            (keycode, down, timeout), where
                keycode (str|KeyCode): pynput key code.
                down (boolean): True means the key will be pressed down,
                    False means the key will be released.
                timeout (int): number of seconds to sleep after
                    the keyboard event.

        """
        cls._log.debug("Keyboard.send_keyboard_events %r", events)
        for event in events:
            (key, down, timeout) = event

            # Raise an error if the key is unsupported. 'key' can also be a
            # string, e.g. "a", "b", "/", etc, but we don't check if those
            # are valid.
            if isinstance(key, KeyCode) and key.vk == -1:
                raise ValueError("Unsupported key: %r" % key.char)

            # Press/release the key, catching any errors.
            try:
                cls._controller.touch(key, down)
            except Exception as e:
                cls._log.exception("Failed to type key code %s: %s",
                                   key, e)

            # Sleep after the keyboard event if necessary.
            if timeout:
                time.sleep(timeout)

    @classmethod
    def get_typeable(cls, char, is_text=False):
        return PynputTypeable(char, is_text=is_text)
