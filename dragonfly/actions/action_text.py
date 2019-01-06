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
"""
Text action
============================================================================

This section describes the :class:`Text` action object. This type of
action is used for typing text into the foreground application.

It differs from the :class:`Key` action in that :class:`Text` is used for
typing literal text, while :class:`dragonfly.actions.action_key.Key`
emulates pressing keys on the keyboard.  An example of this is that the
arrow-keys are not part of a text and so cannot be typed using the
:class:`Text` action, but can be sent by the
:class:`dragonfly.actions.action_key.Key` action.


Windows Unicode Keyboard Support
............................................................................

The :class:`Text` action can be used to type arbitrary Unicode characters
using the `relevant Windows API <https://docs.microsoft.com/en-us/windows/desktop/api/winuser/ns-winuser-tagkeybdinput#remarks>`__.
This is disabled by default because it ignores the up/down status of
modifier keys (e.g. ctrl).

It can be enabled by changing the ``unicode_keyboard`` setting in
`~/.dragonfly2-speech/settings.cfg` to ``True``::

    unicode_keyboard = True


If you need to simulate typing arbitrary Unicode characters *and* have
*individual* :class:`Text` actions respect modifier keys normally for normal
characters, set the configuration as above and use the ``use_hardware``
parameter for :class:`Text` as follows:

.. code:: python

   Text(u"σμ") + Key("ctrl:down") + Text("]", use_hardware=True) + Key("ctrl:up")


Some applications require hardware emulation versus Unicode keyboard
emulation. If you use such applications, add their executable names to the
``hardware_apps`` list in the configuration file mentioned above to make
dragonfly always use hardware emulation for them.


Text class reference
............................................................................

"""


from six import text_type

from ..engines import get_engine
from ..windows.clipboard import Clipboard
from ..windows.window import Window
from .action_base import ActionError, DynStrActionBase
from .action_key import Key
from .keyboard import Keyboard
from .typeables import typeables

# ---------------------------------------------------------------------------

UNICODE_KEYBOARD = False
HARDWARE_APPS = [
            "tvnviewer.exe", "vncviewer.exe", "mstsc.exe", "virtualbox.exe"
        ]


def load_configuration():
    """Locate and load configuration."""
    import io
    import os
    try:
        import configparser
    except ImportError:
        import ConfigParser as configparser

    global UNICODE_KEYBOARD
    global HARDWARE_APPS

    home = os.path.expanduser("~")
    config_folder = os.path.join(home, ".dragonfly2-speech")
    config_file = "settings.cfg"
    config_path = os.path.join(config_folder, config_file)

    if not os.path.exists(config_folder):
        os.mkdir(config_folder)
    if not os.path.exists(config_path):
        with io.open(config_path, "w") as f:
            # Write the default values to the config file.
            f.write(u'[Text]\n')
            f.write(u'hardware_apps = %s\n' % "|".join(HARDWARE_APPS))
            f.write(u'unicode_keyboard = %s\n' % UNICODE_KEYBOARD)

    parser = configparser.ConfigParser()
    parser.read(config_path)
    if parser.has_option("Text", "hardware_apps"):
        HARDWARE_APPS = parser.get("Text", "hardware_apps").lower().split("|")
    if parser.has_option("Text", "unicode_keyboard"):
        UNICODE_KEYBOARD = parser.getboolean("Text", "unicode_keyboard")


load_configuration()


def require_hardware_emulation():
    """Return `True` if the current context requires hardware emulation."""
    from os.path import basename
    foreground_executable = basename(Window.get_foreground()
                                     .executable.lower())
    return (not UNICODE_KEYBOARD) or (foreground_executable in HARDWARE_APPS)


class Text(DynStrActionBase):
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

    _pause_default = 0.02
    _keyboard = Keyboard()
    _specials = {
                 "\n": typeables["enter"],
                 "\t": typeables["tab"],
                }

    def __init__(self, spec=None, static=False, pause=_pause_default,
                 autofmt=False, use_hardware=False):
        self._pause = pause
        self._autofmt = autofmt
        self._use_hardware = use_hardware
        DynStrActionBase.__init__(self, spec=spec, static=static)

    def _parse_spec(self, spec):
        """Convert the given *spec* to keyboard events."""
        from struct import unpack
        events = []
        if self._use_hardware or require_hardware_emulation():
            for character in spec:
                if character in self._specials:
                    typeable = self._specials[character]
                    events.extend(typeable.events(self._pause))
                else:
                    try:
                        typeable = Keyboard.get_typeable(character)
                        events.extend(typeable.events(self._pause))
                    except ValueError:
                        raise ActionError("Keyboard interface cannot type this"
                                          " character: %r (in %r)"
                                          % (character, spec))
        else:
            for character in text_type(spec):
                if character in self._specials:
                    typeable = self._specials[character]
                    events.extend(typeable.events(self._pause))
                else:
                    byte_stream = character.encode("utf-16-le")
                    for short in unpack("<" + str(len(byte_stream) // 2) + "H",
                                        byte_stream):
                        try:
                            typeable = Keyboard.get_typeable(short,
                                                             is_text=True)
                            events.extend(typeable.events(self._pause * 0.5))
                        except ValueError:
                            raise ActionError("Keyboard interface cannot type "
                                              "this character: %r (in %r)" %
                                              (character, spec))
        return events

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
            word = Clipboard.get_text()

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

        # Send keyboard events.
        self._keyboard.send_keyboard_events(events)
        return True
