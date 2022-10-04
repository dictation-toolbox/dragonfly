# encoding: utf-8
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

# pylint: disable=line-too-long

"""
Text action
============================================================================

This section describes the :class:`Text` action object.  This type of action
is used for typing text into the foreground window.

To use this action on X11 (Linux), the
`xdotool <https://www.semicomplete.com/projects/xdotool/>`__ program must be
installed and the ``DISPLAY`` environment variable set.

The :class:`Text` action differs from :class:`Key` in that it is used for
typing literal text, while :class:`Key` emulates pressing keys on the
keyboard.  An example of this is that the arrow-keys are not part of a text
and so cannot be typed using the :class:`Text` action, but can be sent by
the :class:`Key` action.


Unicode Character Keystrokes (Text)
............................................................................

The :class:`Text` action may be used on Windows and X11 (Linux) to type most
Unicode characters (code points).  This feature is not available on macOS.

Please see :ref:`RefUnicodeCharacterKeystrokesKey` for documentation on this
subject.  Most of it applies to :class:`Text` action objects too.


Text class reference
............................................................................

"""

import locale
import six

from dragonfly.actions.action_base           import ActionError
from dragonfly.actions.action_key            import Key
from dragonfly.actions.action_base_keyboard  import BaseKeyboardAction
from dragonfly.engines                       import get_engine
from dragonfly.windows.clipboard             import Clipboard

#---------------------------------------------------------------------------


class Text(BaseKeyboardAction):
    """
    `Action` that sends keyboard events to type text.

    Arguments:
     - *spec* (*str*) -- the text to type
     - *static* (boolean) --
       if *True*, do not dynamically interpret *spec*
       when executing this action
     - *pause* (*float*) --
       the time to pause between each keystroke, given
       in seconds
     - *autofmt* (boolean) --
       if *True*, attempt to format the text with correct
       spacing and capitalization.  This is done by first mimicking
       a word recognition and then analyzing its spacing and
       capitalization and applying the same formatting to the text.
     - *use_hardware* (boolean) --
       if *True*, send keyboard events using hardware emulation instead of
       as Unicode text. This will respect the up/down status of modifier
       keys.
    """

    #: Default time to pause between keystrokes.
    _pause_default =  0.005

    _specials = {
        "\n": "enter",
        "\t": "tab",
    }

    def __init__(self, spec=None, static=False, pause=None,
                 autofmt=False, use_hardware=False):
        if isinstance(spec, six.binary_type):
            spec = spec.decode(locale.getpreferredencoding())
        BaseKeyboardAction.__init__(self, spec=spec, static=static,
                                    use_hardware=use_hardware)
        # Set other members.
        self._autofmt = autofmt
        self._pause = self._pause_default if pause is None else pause

    def _parse_spec(self, spec):
        """Convert the given *spec* to keyboard events."""
        key_symbols = []
        for character in spec:
            # The character is the key symbol, except in special cases.
            if character in self._specials:
                key_symbol = self._specials[character]
            else:
                key_symbol = character

            # Add the key symbol to the list.
            key_symbols.append(key_symbol)

        return key_symbols

    def _execute_events(self, events):
        """
        Send keyboard events.

        If instance was initialized with *autofmt* True,
        then this method will mimic a word recognition
        and analyze its formatting so as to autoformat
        the text's spacing and capitalization before
        sending it as keyboard events.
        """
        if self._autofmt:
            # Mimic a word, select and copy it to retrieve capitalization.
            get_engine().mimic("test")
            Key("cs-left, c-c/5").execute()
            word = Clipboard.get_system_text()

            # Inspect formatting of the mimicked word.
            index = word.find("test")
            if index == -1:
                index = word.find("Test")
                capitalize = True
                if index == -1:
                    self._log.error("Failed to autoformat.")
                    return False
            else:
                capitalize = False

            # Capitalize given text if necessary.
            text = self._spec
            if capitalize:
                text = text[0].capitalize() + text[1:]

            # Reconstruct autoformatted output and convert it
            #  to keyboard events.
            prefix = word[:index]
            suffix = word[index + 4:]
            events = self._parse_spec(prefix + text + suffix)

        # Calculate keyboard events.
        use_hardware = self.require_hardware_events()
        keyboard_events = []
        for key_symbol in events:
            # Get a Typeable object for each key symbol, if possible.
            typeable = self._get_typeable(key_symbol, use_hardware)

            # Raise an error message if a Typeable could not be retrieved.
            if typeable is None:
                error_message = ("Keyboard interface cannot type this"
                                 " character: %r" % key_symbol)
                raise ActionError(error_message)

            # Get keyboard events using the Typeable.
            keyboard_events.extend(typeable.events(self._pause))

        # Send keyboard events.
        self._keyboard.send_keyboard_events(keyboard_events)
        return True

    def __str__(self):
        return u"{!r}".format(self._spec)
