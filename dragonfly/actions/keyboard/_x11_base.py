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

# This file is based on Aenea's X11 key_press implementations.

# pylint: disable=abstract-method

from locale import getpreferredencoding

from six import binary_type
from ._base import BaseKeyboard, BaseTypeable, BaseKeySymbols


KEY_TRANSLATION = {
    # Dragonfly references character keys as characters internally.
    '&': 'ampersand',
    '*': 'asterisk',
    '@': 'at',
    '\\': 'backslash',
    '`': 'grave',
    '|': 'bar',
    '^': 'asciicircum',
    ':': 'colon',
    ',': 'comma',
    '$': 'dollar',
    '.': 'period',
    '"': 'quotedbl',
    '=': 'equal',
    '!': 'exclam',
    '#': 'numbersign',
    '-': 'minus',
    '<': 'less',
    '{': 'braceleft',
    '[': 'bracketleft',
    '(': 'parenleft',
    '%': 'percent',
    '+': 'plus',
    '?': 'question',
    '>': 'greater',
    '}': 'braceright',
    ']': 'bracketright',
    ')': 'parenright',
    ';': 'semicolon',
    '/': 'slash',
    "'": 'apostrophe',
    '~': 'asciitilde',
    '_': 'underscore',
    ' ': 'space',
}


def _update_key_translation(translation):
    caps_keys = [
        'left',
        'right',
        'up',
        'down',
        'home',
        'end',
        'tab',
        'insert',
        'escape'
        ]
    caps_keys.extend('f%i' % i for i in range(1, 13))
    for key in caps_keys:
        translation[key] = key[0].upper() + key[1:]
    for index in range(10):
        translation['np%i' % index] = 'KP_%i' % index
    letters = tuple(range(ord('a'), ord('z')))
    digits = tuple(range(ord('0'), ord('9')))
    for char in letters + digits:
        translation[chr(char)] = chr(char)
        translation[chr(char).upper()] = chr(char).upper()


_update_key_translation(KEY_TRANSLATION)


class X11Typeable(BaseTypeable):
    pass


class BaseX11Keyboard(BaseKeyboard):
    """ Base Keyboard class for X11. """

    @classmethod
    def get_typeable(cls, char, is_text=False):
        """ Get a Typeable object. """
        # Get a key translation if one exists.  Otherwise use the character
        #  as the key name.
        key = KEY_TRANSLATION.get(char, char)
        if isinstance(key, binary_type):
            key = key.decode(getpreferredencoding())

        # Convert single character keys to their Unicode code points.
        #  This allows typing any Unicode character with the Text and Key
        #  actions.  It works with both X11 keyboard implementations.
        if len(key) == 1:
            # Get the Unicode code point for the character.
            encoding = getpreferredencoding()
            code_point = key.encode("unicode_escape")[2:].decode(encoding)

            # Handle ASCII keys by getting the hex code without '0x'.
            if not code_point:
                code_point = hex(ord(key))[2:]

            # Create a key name that xdotool will accept (e.g. U20AC).
            key = 'U' + code_point.upper()
        return X11Typeable(code=key, name=char, is_text=is_text)


class XdoKeySymbols(BaseKeySymbols):
    """ Key symbols for libxdo. """

    # Whitespace and editing keys
    RETURN = 'Return'
    TAB = 'Tab'
    SPACE = 'space'
    BACK = 'BackSpace'
    DELETE = 'Delete'

    # Main modifier keys
    SHIFT = 'Shift_L'
    CONTROL = 'Control_L'
    ALT = 'Alt_L'

    # Right modifier keys
    RSHIFT = 'Shift_R'
    RCONTROL = 'Control_R'
    RALT = 'Alt_R'

    # Special keys
    ESCAPE = 'Escape'
    INSERT = 'Insert'
    PAUSE = 'Pause'
    LSUPER = 'Super_L'
    RSUPER = 'Super_R'
    APPS = 'Menu'
    SNAPSHOT = 'Print'

    # Lock keys
    SCROLL_LOCK = 'Scroll_Lock'
    NUM_LOCK = 'Num_Lock'
    CAPS_LOCK = 'Caps_Lock'

    # Navigation keys
    UP = 'Up'
    DOWN = 'Down'
    LEFT = 'Left'
    RIGHT = 'Right'
    PAGE_UP = 'Prior'
    PAGE_DOWN = 'Next'
    HOME = 'Home'
    END = 'End'

    # Number pad keys
    MULTIPLY = 'KP_Multiply'
    ADD = 'KP_Add'
    SEPARATOR = 'KP_Separator'
    SUBTRACT = 'KP_Subtract'
    DECIMAL = 'KP_Decimal'
    DIVIDE = 'KP_Divide'

    # Number pad number keys
    NUMPAD0 = 'KP_0'
    NUMPAD1 = 'KP_1'
    NUMPAD2 = 'KP_2'
    NUMPAD3 = 'KP_3'
    NUMPAD4 = 'KP_4'
    NUMPAD5 = 'KP_5'
    NUMPAD6 = 'KP_6'
    NUMPAD7 = 'KP_7'
    NUMPAD8 = 'KP_8'
    NUMPAD9 = 'KP_9'

    # Function keys
    F1 = 'F1'
    F2 = 'F2'
    F3 = 'F3'
    F4 = 'F4'
    F5 = 'F5'
    F6 = 'F6'
    F7 = 'F7'
    F8 = 'F8'
    F9 = 'F9'
    F10 = 'F10'
    F11 = 'F11'
    F12 = 'F12'
    F13 = 'F13'
    F14 = 'F14'
    F15 = 'F15'
    F16 = 'F16'
    F17 = 'F17'
    F18 = 'F18'
    F19 = 'F19'
    F20 = 'F20'
    F21 = 'F21'
    F22 = 'F22'
    F23 = 'F23'
    F24 = 'F24'

    # Multimedia keys
    VOLUME_DOWN = 'XF86AudioLowerVolume'
    VOLUME_MUTE = 'XF86AudioMute'
    VOLUME_UP = 'XF86AudioRaiseVolume'
    MEDIA_PREV_TRACK = 'XF86AudioPrev'
    MEDIA_NEXT_TRACK = 'XF86AudioNext'
    MEDIA_PLAY_PAUSE = 'XF86AudioPlay'
    BROWSER_BACK = 'XF86Back'
    BROWSER_FORWARD = 'XF86Forward'
