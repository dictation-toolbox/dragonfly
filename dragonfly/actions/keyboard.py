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
from ctypes import windll, c_char
import win32con
import dragonfly.actions.acstr as acstr
import dragonfly.actions.actionbase as actionbase_
import dragonfly.actions.sendinput as sendinput


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

    def on_events(self):
        events = [(m, True, 0) for m in self._modifiers]
        events.append((self._code, True, 0))
        return events

    def off_events(self):
        events = [(m, False, 0) for m in self._modifiers]
        events.append((self._code, False, 0))
        events.reverse()
        return events

    def events(self):
        events = [(self._code, True, 0), (self._code, False, 0)]
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

        for keycode, down, timeout in events:
            input = sendinput.KeyboardInput(keycode, down)
            array = sendinput.make_input_array([input])
            sendinput.send_input_array(array)
            if timeout: time.sleep(timeout)

    send_keyboard_events = classmethod(send_keyboard_events)


    def get_virtual_keycode(cls, char):
        code = windll.user32.VkKeyScanA(c_char(char))
        if code == -1:
            raise ValueError("Unknown char: %r" % char)

        # Construct a list of the virtual key code and modifiers.
        codes = [code & 0x00ff]
        if   code & 0x0100: codes.append(cls.shift_code)
        elif code & 0x0200: codes.append(cls.ctrl_code)
        elif code & 0x0400: codes.append(cls.alt_code)
        return codes

    get_virtual_keycode = classmethod(get_virtual_keycode)


    def get_keycode_and_modifiers(self, char):
        code = windll.user32.VkKeyScanA(c_char(char))
        if code == -1:
            raise ValueError("Unknown char: %r" % char)

        # Construct a list of the virtual key code and modifiers.
        modifiers = []
        if   code & 0x0100: modifiers.append(self.shift_code)
        elif code & 0x0200: modifiers.append(self.ctrl_code)
        elif code & 0x0400: modifiers.append(self.alt_code)
        code &= 0x00ff
        return code, modifiers


    def get_typeable(self, char):
        code, modifiers = self.get_keycode_and_modifiers(char)
        return Typeable(code, modifiers)


keyboard = Keyboard()


#---------------------------------------------------------------------------
# Virtual key code dictionary.

keycodes = {
        "up":           win32con.VK_UP,
        "down":         win32con.VK_DOWN,
        "left":         win32con.VK_LEFT,
        "right":        win32con.VK_RIGHT,
        "pgup":         win32con.VK_PRIOR,
        "pgdown":       win32con.VK_NEXT,
        "home":         win32con.VK_HOME,
        "end":          win32con.VK_END,
        "shift":        win32con.VK_SHIFT,
        "control":      win32con.VK_CONTROL,
        "ctrl":         win32con.VK_CONTROL,
        "alt":          win32con.VK_MENU,
        "enter":        win32con.VK_RETURN,
        "tab":          win32con.VK_TAB,
        "space":        win32con.VK_SPACE,
        "backspace":    win32con.VK_BACK,
        "bksp":         win32con.VK_BACK,
        "delete":       win32con.VK_DELETE,
        "del":          win32con.VK_DELETE,
        "apps":         win32con.VK_APPS,
        "popup":        win32con.VK_APPS,
        "win":          win32con.VK_LWIN,
        "escape":       win32con.VK_ESCAPE,
        "npmul":        win32con.VK_MULTIPLY,
        "npadd":        win32con.VK_ADD,
        "npsep":        win32con.VK_SEPARATOR,
        "npsub":        win32con.VK_SUBTRACT,
        "npdec":        win32con.VK_DECIMAL,
        "npdiv":        win32con.VK_DIVIDE,
#       "name":         win32con.VK_name,
        }

# Add letters and numbers.
keycodes.update(dict(zip("abcdefghijklmnopqrstuvwxyz", range(0x41, 0x41 + 26))))
keycodes.update(dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", range(0x41, 0x41 + 26))))
keycodes.update(dict(zip("0123456789", range(0x30, 0x30 + 10))))

# Add number pad keys.
keycodes.update(dict([
        ("numpad%s" % n, getattr(win32con, "VK_NUMPAD%s" % n))
        for n in xrange(0, 10)
        ]))

# Add function keys.
keycodes.update(dict([
        ("f%s" % n, getattr(win32con, "VK_F%s" % n))
        for n in xrange(1, 25)
        ]))

# Add specially named keys.
_named_characters = r"""
        `:backtick -:minus,hyphen =:equals
        [:lbracket ]:rbracket \:backslash
        ;:semicolon ':singlequote
        ,:comma .:dot,period /:slash
    """
keycodes.update(dict([
    (n, Keyboard.get_virtual_keycode(c_ns[0])[0])
    for c_ns in _named_characters.split()
    for n in c_ns[2:].split(",")]))


#---------------------------------------------------------------------------

class KeyAction(actionbase_.DynStrActionBase):

    # Various keystroke specification format parameters.
    _key_separator = ","
    _delimiter_characters = ":/"
    _modifier_prefix_delimiter = "-"
    _modifier_prefix_characters = {
        'a': keycodes["alt"],
        'c': keycodes["control"],
        's': keycodes["shift"],
        'w': keycodes["win"],
        }
    _pause_factor = 0.02
    _keyboard = Keyboard()

    def _parse_spec(self, spec):
        # Iterate through the keystrokes specified in spec, parsing
        #  each individually.
        events = []
        for single in spec.split(self._key_separator):
            events.extend(self._parse_single(single))
        return events

    def _parse_single(self, spec):

        # Remove leading and trailing whitespace.
        spec = spec.strip()

        # Parse modifier prefix.
        index = spec.find(self._modifier_prefix_delimiter)
        if index != -1:
            s = spec[:index]
            index += 1
            modifiers = []
            for c in s:
                if c not in self._modifier_prefix_characters:
                    raise acstr.ActionStringError("Invalid modifier"
                                            " prefix character: '%s'" % c)
                m = self._modifier_prefix_characters[c]
                if m in modifiers: raise acstr.ActionStringError(
                            "Double modifier prefix character: '%s'" % c)
                modifiers.append(m)
        else:
            index = 0
            modifiers = ()

        inner_pause = None
        special = None
        outer_pause = None

        delimiters = [(c, i + index) for i, c in enumerate(spec[index:])
                                        if c in self._delimiter_characters]
        delimiter_sequence = "".join([d[0] for d in delimiters])
        delimiter_index = [d[1] for d in delimiters]

        if delimiter_sequence == "":            
            keyname = spec[index:]
        elif delimiter_sequence == "/":
            keyname = spec[index:delimiter_index[0]]
            outer_pause = spec[delimiter_index[0]+1:]
        elif delimiter_sequence == "/:":
            keyname = spec[index:delimiter_index[0]]
            inner_pause = spec[delimiter_index[0]+1:delimiter_index[1]]
            special = spec[delimiter_index[1]+1:]
        elif delimiter_sequence == "/:/":
            keyname = spec[index:delimiter_index[0]]
            inner_pause = spec[delimiter_index[0]+1:delimiter_index[1]]
            special = spec[delimiter_index[1]+1:delimiter_index[2]]
            outer_pause = spec[delimiter_index[2]+1:]
        elif delimiter_sequence == ":":
            keyname = spec[index:delimiter_index[0]]
            special = spec[delimiter_index[0]+1:]
        elif delimiter_sequence == ":/":
            keyname = spec[index:delimiter_index[0]]
            special = spec[delimiter_index[0]+1:delimiter_index[1]]
            outer_pause = spec[delimiter_index[1]+1:]

        try: code = keycodes[keyname]
        except KeyError: raise acstr.ActionStringError("Invalid key name: '%s'"
                                                            % keyname)


        if inner_pause is not None:
            s = inner_pause
            try:
                inner_pause = float(s) * self._pause_factor
                if inner_pause < 0: raise ValueError
            except ValueError:
                raise acstr.ActionStringError("Invalid inner pause value: '%s',"
                                        " should be a positive number." % s)
        if outer_pause is not None:
            s = outer_pause
            try:
                outer_pause = float(s) * self._pause_factor
                if outer_pause < 0: raise ValueError
            except ValueError:
                raise acstr.ActionStringError("Invalid outer pause value: '%s',"
                                        " should be a positive number." % s)

        direction = None; repeat = 1
        if special is not None:
            if special == "down":   direction = True
            elif special == "up":   direction = False
            else:
                s = special
                try:
                    repeat = int(s)
                    if repeat < 0: raise ValueError
                except ValueError:
                    raise acstr.ActionStringError("Invalid repeat value: '%s',"
                                    " should be a positive integer." % s)

        if direction is None:
            if repeat == 0:
                events = []
            else:
                events = [(m, True, None) for m in modifiers]
                events += [(code, True, None),
                           (code, False, inner_pause)] * repeat
                events[-1] = (code, False, outer_pause)
                events += [(m, False, None) for m in modifiers[-1::-1]]
        else:
            if modifiers: raise acstr.ActionStringError(
                                "Cannot use direction with modifiers.")
            if inner_pause is not None: raise acstr.ActionStringError(
                                "Cannot use direction with inner pause.")
            events = [(code, direction, outer_pause)]

        return events

    def _execute_events(self, events):
        self._keyboard.send_keyboard_events(events)
        return True


#---------------------------------------------------------------------------

class TextAction(actionbase_.DynStrActionBase):

    _pause_factor = 0.02
    _keyboard = Keyboard()
    _specials = {
        "\n":   [keycodes["enter"]],
        "\t":   [keycodes["tab"]],
        }

    def _parse_spec(self, spec):
        events = []
        for character in spec:
            if character in self._specials:
                codes = self._specials[character]
            else:
                codes = Keyboard.get_virtual_keycode(character)
                if 0 :
                    raise ValueError("Invalid character: %r, code %d" \
                                                % (character, code))
            code = codes[0]
            modifiers = codes[1:]

            character_events = [(code, True, None), (code, False, None)]

            for modifier in modifiers:
                character_events.insert(0, (modifier, True,  None))
                character_events.append(   (modifier, False, None))

            c, d, p = character_events[-1]
            character_events[-1] = (c, d, self._pause_factor)

            events.extend(character_events)

        return events

    def _execute_events(self, events):
        self._keyboard.send_keyboard_events(events)
        return True
