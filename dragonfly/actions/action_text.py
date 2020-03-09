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

This section describes the :class:`Text` action object. This type of
action is used for typing text into the foreground application.  This works
on Windows, Mac OS and with X11 (e.g. on Linux).

To use this class on X11/Linux, the
`xdotool <https://www.semicomplete.com/projects/xdotool/>`__ program must be
installed.

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

   action = Text("σμ") + Key("ctrl:down") + Text("]", use_hardware=True) + Key("ctrl:up")
   action.execute()


Some applications require hardware emulation versus Unicode keyboard
emulation. If you use such applications, add their executable names to the
``hardware_apps`` list in the configuration file mentioned above to make
dragonfly always use hardware emulation for them.

If hardware emulation is required, then the action will use the keyboard
layout of the foreground window when calculating keyboard events. If any of
the specified characters are not typeable using the current window's
keyboard layout, then an error will be logged and no keys will be typed::

    action.exec (ERROR): Execution failed: Keyboard interface cannot type this character: 'c'

These settings and parameters have no effect on other platforms.


X11/Linux Unicode Keyboard Support
............................................................................

The :class:`Text` action can also type arbitrary Unicode characters on X11.
This works regardless of the ``use_hardware`` parameter or
``unicode_keyboard`` setting.

Unlike on Windows, modifier keys will be respected by :class:`Text` actions
on X11. As such, the previous Windows example will work and can even be
simplified a little:

.. code:: python

   action = Text("σμ") + Key("ctrl:down") + Text("]") + Key("ctrl:up")
   action.execute()


It can also be done with one :class:`Key` action:

.. code:: python

   Key("σ,μ,c-]").execute()


Text class reference
............................................................................

"""

from locale import getpreferredencoding
import sys

from six import binary_type

from ..engines import get_engine
from ..util.clipboard import Clipboard
from .action_base import ActionError
from .action_base_keyboard import BaseKeyboardAction
from .action_key import Key
from .typeables import typeables

# ---------------------------------------------------------------------------

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

    class Events(object):
        def __init__(self,
                     hardware_events,
                     hardware_error_message,
                     unicode_events,
                     unicode_error_message):
            self.hardware_events = hardware_events
            self.hardware_error_message = hardware_error_message
            self.unicode_events = unicode_events
            self.unicode_error_message = unicode_error_message

    _specials = {
        "\n": typeables["enter"],
        "\t": typeables["tab"],
    }

    def __init__(self, spec=None, static=False, pause=None,
                 autofmt=False, use_hardware=False):
        # Use the default pause time if pause in None.
        # Use the class's _pause_default value so that Text sub-classes can
        # easily override it.
        self._pause = self._pause_default if pause is None else pause

        # Set other members and call the super constructor.
        self._autofmt = autofmt
        self._on_windows = sys.platform.startswith("win")

        if isinstance(spec, binary_type):
            spec = spec.decode(getpreferredencoding())

        BaseKeyboardAction.__init__(self, spec=spec, static=static,
                                    use_hardware=use_hardware)

    def _parse_spec(self, spec):
        """Convert the given *spec* to keyboard events."""
        hardware_events = []
        unicode_events = []
        hardware_error_message = None
        unicode_error_message = None

        for character in spec:
            if character in self._specials:
                typeable = self._specials[character]
                hardware_events.extend(typeable.events(self._pause))
                unicode_events.extend(typeable.events(self._pause))
            else:
                # Add hardware events.
                try:
                    typeable = self._keyboard.get_typeable(character)
                    hardware_events.extend(typeable.events(self._pause))
                except ValueError:
                    hardware_error_message = ("Keyboard interface cannot type this"
                                              " character: %r (in %r)"
                                              % (character, spec))

                # Calculate and add Unicode events only if necessary.
                if not self._on_windows or self._use_hardware:
                    continue

                try:
                    typeable = self._keyboard.get_typeable(character,
                                                           is_text=True)
                    unicode_events.extend(typeable.events(self._pause * 0.5))
                except ValueError:
                    unicode_error_message = ("Keyboard interface cannot type "
                                             "this character: %r (in %r)" %
                                             (character, spec))
        return self.Events(hardware_events, hardware_error_message,
                           unicode_events, unicode_error_message)

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

        # Send keyboard events.
        if self.require_hardware_events():
            error_message = events.hardware_error_message
            keyboard_events = events.hardware_events
        else:
            error_message = events.unicode_error_message
            keyboard_events = events.unicode_events
        if error_message:
            raise ActionError(error_message)
        else:
            self._keyboard.send_keyboard_events(keyboard_events)
        return True

    def __str__(self):
        return u"{!r}".format(self._spec)
