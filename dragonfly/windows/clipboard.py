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
This file implements an interface to the system clipboard using pyperclip
and should work on Windows, Mac OS and Linux-based operating systems.
"""


import pyperclip

#===========================================================================

class Clipboard(object):
    """
    This class provides multi-platform clipboard support through pyperclip.
    The only currently supported Windows clipboard format is Unicode text.
    """

    #-----------------------------------------------------------------------

    format_unicode = 13  # retrieved from pyperclip.init_windows_clipboard
    format_names = {format_unicode: "unicode"}

    @classmethod
    def get_system_text(cls):
        return pyperclip.paste()

    @classmethod
    def set_system_text(cls, content):
        pyperclip.copy(content)

    @classmethod
    def clear_clipboard(cls):
        # TODO Perhaps keep a Windows-only implementation for this;
        # setting to "" is not technically the same as using
        # win32clipboard.EmptyClipboard.
        pyperclip.copy("")

    #-----------------------------------------------------------------------

    def __init__(self, contents=None, text=None, from_system=False):
        # Handle a dictionary argument for contents.
        if contents and isinstance(contents, dict):
            content = None
            for k in contents.keys():
                # Only accept the unicode format for the moment.
                if k == self.format_unicode:
                    content = contents[k]
        else:
            content = None

        self._content = content

        # If requested, retrieve current system clipboard contents.
        if from_system:
            self.copy_from_system()

        # Handle text content.
        if text is not None:
            self._content = unicode(text)

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._content)

    def copy_from_system(self, formats=None, clear=False):
        """
            Copy the system clipboard contents into this instance.

            Arguments:
             - *formats* (iterable, default: None) -- this argument has
               been *deprecated* and has no effect.
             - *clear* (boolean, default: False) -- if true, the system
               clipboard will be cleared after its contents have been
               retrieved.

        """
        # Retrieve the system clipboard content.
        self._content = pyperclip.paste()

        # Then clear the system clipboard, if requested.
        if clear:
            self.clear_clipboard()

    def copy_to_system(self, clear=True):
        """
            Copy the contents of this instance into the system clipboard.

            Arguments:
             - *clear* (boolean, default: True) -- this argument has been
               *deprecated*: the pyperclip implementation for Windows
               always clears the clipboard before copying.

        """
        # Transfer content to system clipboard.
        pyperclip.copy(self._content)

    def has_format(self, format):
        """
            Determine whether this instance has content for the given
            *format*.

            Arguments:
             - *format* (int) -- the clipboard format to look for.

        """
        return format == self.format_unicode and self._content

    def get_format(self, format):
        """
            Retrieved this instance's content for the given *format*.

            Only Unicode format (13) is currently supported.
            If the given *format* is not available, a *ValueError*
            is raised.

            Arguments:
             - *format* (int) -- the clipboard format to retrieve.
        """
        if format == self.format_unicode:
            return self._content
        else:
            raise ValueError("Clipboard format not available: %r"
                             % format)

    def set_format(self, format, content):
        """

            Set this instance's content for the given *format*.

            Only Unicode format (13) is currently supported.
            If the given *format* is not available, a *ValueError*
            is raised.

            Arguments:
             - *content* (string) -- the clipboard contents to set.
             - *format* (int) -- the clipboard format to set.
        """
        pass

    def has_text(self):
        """ Determine whether this instance has text content. """
        return bool(self._content)

    def get_text(self):
        """
            Retrieve this instance's text content.  If no text content
            is available, this method returns *None*.

        """
        return None if not self._content else self._content

    def set_text(self, content):
        self._content = unicode(content)

    text = property(
                    lambda self: self.get_text(),
                    lambda self, d: self.set_text(d)
                   )
