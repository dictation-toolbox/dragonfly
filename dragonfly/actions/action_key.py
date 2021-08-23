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
.. _RefKey:

Key action
============================================================================

This section describes the :class:`Key` action object.  This
type of action is used for sending keystrokes to the foreground
application.  This works on Windows, Mac OS and with X11 (e.g. on Linux).
Examples of how to use this class are given in :ref:`RefKeySpecExamples`.

To use this class on X11/Linux, the
`xdotool <https://www.semicomplete.com/projects/xdotool/>`__ program must be
installed and the ``XDG_SESSION_TYPE`` environment variable set to ``x11``.
This class does **not** support typing keys in Wayland sessions.

.. _RefKeySpec:

Keystroke specification format
............................................................................

The *spec* argument passed to the :class:`Key` constructor specifies which
keystroke events will be emulated.  It is a string consisting of one or
more comma-separated keystroke elements.  Each of these elements has one
of the following two possible formats:

Normal press-release key action, optionally repeated several times:
   [*modifiers* ``-``] *keyname* [``/`` *innerpause*] [``:`` *repeat*] [``/`` *outerpause*]

Press-and-hold a key, or release a held-down key:
   [*modifiers* ``-``] *keyname* ``:`` *direction* [``/`` *outerpause*]

The different parts of the keystroke specification are as follows.  Note
that only *keyname* is required; the other fields are optional.

 - *modifiers* --
   Modifiers for this keystroke.  These keys are held down
   while pressing the main keystroke.
   Can be zero or more of the following:

    - ``a`` -- alt key
    - ``c`` -- control key
    - ``s`` -- shift key
    - ``w`` -- Windows key

 - *keyname* --
   Name of the keystroke.  Valid names are listed in
   :ref:`RefKeySpecNames`.
 - *innerpause* --
   The time to pause between repetitions of this keystroke.
   It should be given in hundredths of a second.  For
   example, "20" will pause for 20/100s = 0.2 seconds.
 - *repeat* --
   The number of times this keystroke should be repeated.
   If not specified, the key will be pressed and released once.
 - *outerpause* --
   The time to pause after this keystroke.
   It should be given in hundredths of a second.  For
   example, "20" will pause for 20/100s = 0.2 seconds.
 - *direction* --
   Whether to press-and-hold or release the key.  Must be
   one of the following:

    - ``down`` -- press and hold the key
    - ``up`` -- release the key

   Note that releasing a key which is *not* being held down does *not*
   cause an error.  It harmlessly does nothing.


.. _RefKeySpecNames:

Key names
............................................................................

 - Lowercase letter keys: ``a`` or ``alpha``, ``b`` or ``bravo``,
   ``c`` or ``charlie``, ``d`` or ``delta``, ``e`` or ``echo``,
   ``f`` or ``foxtrot``, ``g`` or ``golf``, ``h`` or ``hotel``,
   ``i`` or ``india``, ``j`` or ``juliet``, ``k`` or ``kilo``,
   ``l`` or ``lima``, ``m`` or ``mike``, ``n`` or ``november``,
   ``o`` or ``oscar``, ``p`` or ``papa``, ``q`` or ``quebec``,
   ``r`` or ``romeo``, ``s`` or ``sierra``, ``t`` or ``tango``,
   ``u`` or ``uniform``, ``v`` or ``victor``, ``w`` or ``whisky``,
   ``x`` or ``xray``, ``y`` or ``yankee``, ``z`` or ``zulu``
 - Uppercase letter keys: ``A`` or ``Alpha``, ``B`` or ``Bravo``,
   ``C`` or ``Charlie``, ``D`` or ``Delta``, ``E`` or ``Echo``,
   ``F`` or ``Foxtrot``, ``G`` or ``Golf``, ``H`` or ``Hotel``,
   ``I`` or ``India``, ``J`` or ``Juliet``, ``K`` or ``Kilo``,
   ``L`` or ``Lima``, ``M`` or ``Mike``, ``N`` or ``November``,
   ``O`` or ``Oscar``, ``P`` or ``Papa``, ``Q`` or ``Quebec``,
   ``R`` or ``Romeo``, ``S`` or ``Sierra``, ``T`` or ``Tango``,
   ``U`` or ``Uniform``, ``V`` or ``Victor``, ``W`` or ``Whisky``,
   ``X`` or ``Xray``, ``Y`` or ``Yankee``, ``Z`` or ``Zulu``
 - Number keys: ``0`` or ``zero``, ``1`` or ``one``, ``2`` or ``two``,
   ``3`` or ``three``, ``4`` or ``four``, ``5`` or ``five``,
   ``6`` or ``six``, ``7`` or ``seven``, ``8`` or ``eight``,
   ``9`` or ``nine``
 - Symbol keys: ``!`` or ``bang`` or ``exclamation``, ``@`` or ``at``,
   ``#`` or ``hash``, ``$`` or ``dollar``, ``%`` or ``percent``,
   ``^`` or ``caret``, ``&`` or ``and`` or ``ampersand``,
   ``*`` or ``star`` or ``asterisk``,
   ``(`` or ``leftparen`` or ``lparen``,
   ``)`` or ``rightparen`` or ``rparen``, ``minus`` or ``hyphen``,
   ``_`` or ``underscore``, ``+`` or ``plus``, ````` or ``backtick``,
   ``~`` or ``tilde``, ``[`` or ``leftbracket`` or ``lbracket``,
   ``]`` or ``rightbracket`` or ``rbracket``,
   ``{`` or ``leftbrace`` or ``lbrace``,
   ``}`` or ``rightbrace`` or ``rbrace``, ``\\`` or ``backslash``,
   ``|`` or ``bar``, ``colon``, ``;`` or ``semicolon``,
   ``'`` or ``apostrophe`` or ``singlequote`` or ``squote``,
   ``"`` or ``quote`` or ``doublequote`` or ``dquote``, ``comma``,
   ``.`` or ``dot``, ``slash``,
   ``<`` or ``lessthan`` or ``leftangle`` or ``langle``,
   ``>`` or ``greaterthan`` or ``rightangle`` or ``rangle``,
   ``?`` or ``question``, ``=`` or ``equal`` or ``equals``
 - Whitespace and editing keys: ``enter``, ``tab``, ``space``,
   ``backspace``, ``delete`` or ``del``
 - Main modifier keys: ``shift``, ``control`` or ``ctrl``, ``alt``
 - Right modifier keys: ``rshift``, ``rcontrol`` or ``rctrl``, ``ralt``
 - Special keys: ``escape``, ``insert``, ``pause``, ``win``, ``rwin``,
   ``apps`` or ``popup``, ``snapshot`` or ``printscreen``
 - Lock keys: ``scrolllock``, ``numlock``, ``capslock``
 - Navigation keys: ``up``, ``down``, ``left``, ``right``,
   ``pageup`` or ``pgup``, ``pagedown`` or ``pgdown``, ``home``, ``end``
 - Number pad keys: ``npmul``, ``npadd``, ``npsep``, ``npsub``,
   ``npdec``, ``npdiv``, ``numpad0`` or ``np0``, ``numpad1`` or ``np1``,
   ``numpad2`` or ``np2``, ``numpad3`` or ``np3``,
   ``numpad4`` or ``np4``, ``numpad5`` or ``np5``,
   ``numpad6`` or ``np6``, ``numpad7`` or ``np7``,
   ``numpad8`` or ``np8``, ``numpad9`` or ``np9``
 - Function keys: ``f1``, ``f2``, ``f3``, ``f4``, ``f5``, ``f6``,
   ``f7``, ``f8``, ``f9``, ``f10``, ``f11``, ``f12``, ``f13``, ``f14``,
   ``f15``, ``f16``, ``f17``, ``f18``, ``f19``, ``f20``, ``f21``,
   ``f22``, ``f23``, ``f24``
 - Multimedia keys: ``volumeup`` or ``volup``,
   ``volumedown`` or ``voldown``, ``volumemute`` or ``volmute``,
   ``tracknext``, ``trackprev``, ``playpause``, ``browserback``,
   ``browserforward``


.. _RefKeySpecExamples:

Example key actions
............................................................................

The following code types the text "Hello world!" into the foreground
application: ::

    Key("H, e, l, l, o, space, w, o, r, l, d, exclamation").execute()

The following code is a bit more useful, as it saves the current file with
the name "dragonfly.txt" (this works for many English-language
applications): ::

    action = Key("a-f, a/50") + Text("dragonfly.txt") + Key("enter")
    action.execute()

The following code selects the next four lines by holding down the *shift*
key, slowly moving down 4 lines, and then releasing the *shift* key: ::

    Key("shift:down, down/25:4, shift:up").execute()

The following code locks the screen by pressing the *Windows* key together
with the *l* key: ::

    Key("w-l").execute()


Windows key support
............................................................................

Keyboard events sent by :class:`Key` actions on Windows are calculated using
the current foreground window's keyboard layout. The class will fallback on
Unicode events for keys not typeable with the current layout.

The :class:`Key` action can be used to type arbitrary Unicode characters on
Windows using the `relevant Windows API
<https://docs.microsoft.com/en-us/windows/desktop/api/winuser/ns-winuser-tagkeybdinput#remarks>`__.
This is disabled by default because it ignores the up/down status of
modifier keys (e.g. ctrl).

It can be enabled by changing the ``unicode_keyboard`` setting in
`~/.dragonfly2-speech/settings.cfg` to ``True``: ::

    unicode_keyboard = True

The ``use_hardware`` parameter can be set to ``True`` if you need to
selectively require hardware events for a :class:`Key` action: ::

    # Passing use_hardware=True will guarantee that Ctrl+C is always
    # pressed, regardless of the layout. See below.
    Key("c-c", use_hardware=True).execute()

If the Unicode keyboard is not enabled or the ``use_hardware`` parameter is
``True``, then no keys will be typed and an error will be logged for
untypeable keys: ::

   action.exec (ERROR): Execution failed: Keyboard interface cannot type this character: 'μ'

Keys in ranges 0-9, a-z and A-Z are always typeable. If keys in these ranges
cannot be typed using the current keyboard layout, then the equivalent key
will be used instead. For example, the following code will result in the 'я'
key being pressed when using the main Cyrillic keyboard layout: ::

   # This is equivalent to Key(u"я, Я, c-я").
   Key("z, Z, c-z", use_hardware=True).execute()

Unlike the :class:`Text` action, individual :class:`Key` actions can send
both hardware *and* Unicode events. So the following example will work if
the Unicode keyboard is enabled: ::

    # Type 'σμ' and then press Ctrl+Z.
    Key(u"σ, μ, c-z").execute()


X11 key support
............................................................................

The :class:`Key` action can be used to type arbitrary keys and Unicode
characters on X11/Linux. It is not limited to the key names listed above,
although all of them will work too.

Unicode characters are supported on X11 by passing their Unicode code point
to the keyboard implementation. For example, the character ``'€'`` is
converted to ``'U20AC'``. The Unicode code point can also be passed
directly, e.g. with ``Key('U20AC')``.

Unlike on Windows, the :class:`Key` action is able to use modifiers with
Unicode characters on X11.

This class does **not** support typing keys in Wayland sessions.


Example X11 key actions
----------------------------------------------------------------------------

In addition to the examples in the previous section, the following example
will work on X11/Linux.

The following code will type 'σμ' into the foreground application and then
press ctrl+z: ::

    Key("σ,μ,c-z").execute()

The following code will press 'µ' while holding control and alt: ::

    Key("ca-μ").execute()

The following code will press the browser refresh multimedia key: ::

    Key("XF86Refresh").execute()

Although this key is not defined in dragonfly's typeables list, it still
works because it is passed directly to xdotool. X11 (Xorg) multimedia keys
can be found online: `XF86 keyboard symbols
<https://wiki.linuxquestions.org/wiki/XF86_keyboard_symbols>`__.


Key class reference
............................................................................

"""

import collections

from .action_base           import ActionError
from .action_base_keyboard  import BaseKeyboardAction
from .typeables             import typeables

#---------------------------------------------------------------------------


class Key(BaseKeyboardAction):
    """
        Keystroke emulation action.

        Constructor arguments:
         - *spec* (*str*) -- keystroke specification
         - *static* (boolean) -- flag indicating whether the
           specification contains dynamic elements
         - *use_hardware* (boolean) --
           if *True*, send keyboard events using hardware emulation instead
           of as Unicode text. This will respect the up/down status of
           modifier keys.

        The format of the keystroke specification *spec* is described in
        :ref:`RefKeySpec`.

        This class emulates keyboard activity by sending keystrokes to the
        foreground application.  It does this using Dragonfly's keyboard
        interface for the current platform.  The implementation for Windows
        uses the ``sendinput()`` Win32 API function.  The implementation
        for Mac OS uses
        `pynput <https://pynput.readthedocs.io/en/latest/>`__. The
        implementation for X11/Linux uses `xdotool
        <https://www.semicomplete.com/projects/xdotool/>`__.

    """

    # Various keystroke specification format parameters.
    _key_separator = ","
    _delimiter_characters = ":/"
    _modifier_prefix_delimiter = "-"
    _modifier_prefix_characters = {
        'a': typeables["alt"],
        'c': typeables["control"],
        's': typeables["shift"],
        'w': typeables["win"],
        }
    interval_factor = 0.01
    interval_default = 0.0

    # Keystroke event data type.
    EventData = collections.namedtuple(
        "EventData", "keyname "
                     "direction "
                     "modifiers "
                     "inner_pause "
                     "repeat "
                     "outer_pause "
    )

    def _parse_spec(self, spec):
        # Iterate through the keystrokes specified in spec, parsing
        #  each individually.
        events = []
        for single in spec.split(self._key_separator):
            event_data = self._parse_single(single)
            if not event_data:
                continue
            events.append(event_data)
        return events

    def _parse_single(self, spec):
        # pylint: disable=R0912,R0914,R0915
        # Suppress warnings about too many branches, variables and
        # statements.

        # Remove leading and trailing whitespace.
        spec = spec.strip()
        if not spec:
            return None

        # Parse modifier prefix.
        index = spec.find(self._modifier_prefix_delimiter)
        if index != -1:
            s = spec[:index]
            index += 1
            modifiers = []
            for c in s:
                if c not in self._modifier_prefix_characters:
                    raise ActionError("Invalid modifier"
                                      " prefix character: %r" % c)
                m = self._modifier_prefix_characters[c]
                if m in modifiers:
                    raise ActionError("Double modifier"
                                      " prefix character: %r" % c)
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
        else:
            raise ActionError("Invalid key spec: %s" % spec)

        if inner_pause is not None:
            s = inner_pause
            try:
                inner_pause = float(s) * self.interval_factor
                if inner_pause < 0: raise ValueError
            except ValueError:
                raise ActionError("Invalid inner pause value: %r,"
                                  " should be a positive number." % s)
        if outer_pause is not None:
            s = outer_pause
            try:
                outer_pause = float(s) * self.interval_factor
                if outer_pause < 0: raise ValueError
            except ValueError:
                raise ActionError("Invalid outer pause value: %r,"
                                  " should be a positive number." % s)
        else:
            outer_pause = self.interval_default * self.interval_factor

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
                    raise ActionError("Invalid repeat value: %r,"
                                      " should be a positive integer." % s)

        if direction is not None:
            if modifiers:
                raise ActionError("Cannot use direction with modifiers.")
            if inner_pause is not None:
                raise ActionError("Cannot use direction with inner pause.")

        return self.EventData(keyname, direction, modifiers, inner_pause,
                              repeat, outer_pause)

    def _execute_events(self, events):
        # Calculate keyboard events from events (event data).
        use_hardware = self.require_hardware_events()
        keyboard_events = []
        for event_data in events:
            events_single = self._calc_events_single(event_data,
                                                     use_hardware)
            keyboard_events.extend(events_single)

        # Send keyboard events.
        self._keyboard.send_keyboard_events(keyboard_events)
        return True

    def _calc_events_single(self, event_data, use_hardware):
        (keyname, direction, modifiers, inner_pause, repeat,
         outer_pause) = event_data

        # Get a Typeable object for the key, if possible.
        typeable = self._get_typeable(event_data.keyname, use_hardware)

        # Raise an error message if a Typeable could not be retrieved.
        if typeable is None:
            error_message = ("Keyboard interface cannot type this "
                             "character: %r (in %r)" %
                             (keyname, self._spec))
            raise ActionError(error_message)

        # Calculate keyboard events using the Typeable and event data.
        if direction is None:
            if inner_pause is None:
                inner_pause = self.interval_default * self.interval_factor
            if repeat == 0:
                events = []
            else:
                events = []
                for m in modifiers:
                    events.extend(m.on_events())
                for _ in range(repeat - 1):
                    events.extend(typeable.events(inner_pause))
                events.extend(typeable.events(outer_pause))
                for m in modifiers[-1::-1]:
                    events.extend(m.off_events())
        else:
            if direction:
                events = typeable.on_events(outer_pause)
            else:
                events = typeable.off_events(outer_pause)
        return events

    def __str__(self):
        return '[{!r}]'.format(self._spec)
