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
This file implements the Paste action.
"""


import win32con
from dragonfly.actions.actionbase import DynStrActionBase, ActionError
from dragonfly.actions.action_key import Key
from dragonfly.actions.action_text import Text
from dragonfly.windows.clipboard import Clipboard


#---------------------------------------------------------------------------

class Paste(DynStrActionBase):

    """
        Paste-from-clipboard action.

        Constructor arguments:
         * ``content`` -- content paste.
         * ``format`` -- clipboard format.  Default: Unicode text.
         * ``paste`` -- paste action.  Default: Key("c-v").
         * ``static`` -- flag indicating whether the
           specification contains dynamic elements.  Default: False.

    """

    # Default paste action.
    _default_format = win32con.CF_UNICODETEXT
    _default_paste = Key("c-v/5")

    def __init__(self, content, format=None, paste=None, static=False):
        if not format: format = self._default_format
        if not paste: paste = self._default_paste
        if isinstance(content, basestring):
            spec = content
            self.content = None
        else:
            spec = ""
            self.content = content
        self.format = format
        self.paste = paste
        DynStrActionBase.__init__(self, spec, static=static)

    def _parse_spec(self, spec):
        if self.content:
            return self.content
        else:
            return spec

    def _execute_events(self, events):
        original = Clipboard()
        original.get()

        if self.format == win32con.CF_UNICODETEXT:
            events = unicode(events)
        elif self.format == win32con.CF_TEXT:
            events = str(events)

        clipboard = Clipboard(content=events, format=self.format)
        clipboard.set()
        self.paste.execute()

        original.set()
        return True
