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
application.  Examples of how to use this class are given in
:ref:`RefKeySpecExamples`.


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
 - *repeat* --
   The number of times this keystroke should be repeated.
   If not specified, the key will be pressed and released once.
 - *outerpause* --
   The time to pause after this keystroke.
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
 - Symbol keys: ``bang`` or ``exclamation``, ``at``, ``hash``,
   ``dollar``, ``percent``, ``caret``, ``and`` or ``ampersand``,
   ``star`` or ``asterisk``, ``leftparen`` or ``lparen``,
   ``rightparen`` or ``rparen``, ``minus`` or ``hyphen``,
   ``underscore``, ``plus``, ``backtick``, ``tilde``,
   ``leftbracket`` or ``lbracket``, ``rightbracket`` or ``rbracket``,
   ``leftbrace`` or ``lbrace``, ``rightbrace`` or ``rbrace``,
   ``backslash``, ``bar``, ``colon``, ``semicolon``,
   ``apostrophe`` or ``singlequote`` or ``squote``,
   ``quote`` or ``doublequote`` or ``dquote``, ``comma``, ``dot``,
   ``slash``, ``lessthan`` or ``leftangle`` or ``langle``,
   ``greaterthan`` or ``rightangle`` or ``rangle``, ``question``,
   ``equal`` or ``equals``
 - Whitespace and editing keys: ``enter``, ``tab``, ``space``,
   ``backspace``, ``delete`` or ``del``
 - Modifier keys: ``shift``, ``control`` or ``ctrl``, ``alt``
 - Special keys: ``escape``, ``insert``, ``pause``, ``win``,
   ``apps`` or ``popup``
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
with the *l*: ::

    Key("w-l").execute()


Key class reference
............................................................................

"""


from .action_base  import DynStrActionBase, ActionError
from .typeables    import typeables
from .keyboard     import Keyboard


#---------------------------------------------------------------------------

class Key(DynStrActionBase):

    """
        Keystroke emulation action.

        Constructor arguments:
         - *spec* (*str*) -- keystroke specification
         - *static* (boolean) -- flag indicating whether the
           specification contains dynamic elements

        The format of the keystroke specification *spec* is described in 
        :ref:`RefKeySpec`.

        This class emulates keyboard activity by sending keystrokes to the 
        foreground application.  It does this using Dragonfly's keyboard 
        interface implemented in the :mod:`keyboard` and :mod:`sendinput` 
        modules.  These use the ``sendinput()`` function of the Win32 API.

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
        if not spec:
            return []

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

        try:
            code = typeables[keyname]
        except KeyError:
            raise ActionError("Invalid key name: %r" % keyname)


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

        if direction is None:
            if inner_pause is None:
                inner_pause = self.interval_default * self.interval_factor
            if repeat == 0:
                events = []
            else:
                events = []
                for m in modifiers:
                    events.extend(m.on_events())
                for i in range(repeat - 1):
                    events.extend(code.events(inner_pause))
                events.extend(code.events(outer_pause))
                for m in modifiers[-1::-1]:
                    events.extend(m.off_events())
        else:
            if modifiers:
                raise ActionError("Cannot use direction with modifiers.")
            if inner_pause is not None:
                raise ActionError("Cannot use direction with inner pause.")
            if direction:
                events = code.on_events(outer_pause)
            else:
                events = code.off_events(outer_pause)

        return events

    def _execute_events(self, events):
        self._keyboard.send_keyboard_events(events)
        return True
