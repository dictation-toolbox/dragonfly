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
Paste action
============================================================================

"""

import sys

from six import string_types

from ..actions.action_base import ActionError, DynStrActionBase
from ..actions.action_key import Key
from ..windows.clipboard import Clipboard


#---------------------------------------------------------------------------

class Paste(DynStrActionBase):

    """
        Paste-from-clipboard action.

        Constructor arguments:
         - *contents* (*str* | *dict*) -- contents to paste.  This may be a
           simple string to paste, a dynamic action *spec* or a dictionary
           of clipboard format ints to contents (typically strings).
         - *format* (*int*, clipboard format integer) --
           clipboard format.  This argument is ignored if *contents* is a
           dictionary.
         - *paste* (instance derived from *ActionBase*) --
           paste action
         - *static* (boolean) --
           flag indicating whether the
           specification contains dynamic elements

        This action inserts the given *contents* into the system
        clipboard, and then performs the *paste* action to paste it into
        the foreground application.  By default, the *paste* action is the
        :kbd:`Ctrl-v` keystroke or :kbd:`Super-v` on a mac.  The default
        clipboard format used by this action is the *Unicode* text format.

    """

    _default_format = Clipboard.format_unicode

    # Default paste action spec.
    _default_paste_spec = "w-v/20" if sys.platform == "darwin" else "c-v/20"

    # pylint: disable=redefined-builtin
    def __init__(self, contents, format=None, paste=None, static=False):
        if not format:
            format = self._default_format
        if paste is None:
            # Pass use_hardware=True to guarantee that Ctrl+V is always
            # pressed, regardless of the keyboard layout.
            paste = Key(self._default_paste_spec, use_hardware=True)
        if isinstance(contents, string_types):
            spec = contents
            self.contents = None
        else:
            spec = ""
            self.contents = contents
        self.format = format
        self.paste = paste
        DynStrActionBase.__init__(self, spec, static=static)

    def _parse_spec(self, spec):
        if self.contents:
            return self.contents
        else:
            return spec

    def _execute_events(self, events):
        original = Clipboard()
        try:
            original.copy_from_system()
        except Exception as e:
            self._log.warning("Failed to store original clipboard contents:"
                              " %s", e)

        # Store the contents to copy (i.e. *events*) in a Clipboard
        #  instance using the specified (or default) format.  If *events* is
        #  a dictionary, then pass it instead.
        if isinstance(events, dict):
            clipboard = Clipboard(contents=events)
        else:
            clipboard = Clipboard(contents={self.format: events})

        # Copy the contents to the system clipboard and paste using the
        #  paste action.
        clipboard.copy_to_system()
        self.paste.execute()

        # Restore the original clipboard contents afterwards.  This should
        #  clear the clipboard if we failed to store the original contents
        #  above.
        original.copy_to_system()
        return True
