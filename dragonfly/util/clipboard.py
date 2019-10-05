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


from six import text_type
import pyperclip


class BaseClipboard(object):
    @classmethod
    def get_system_text(cls):
        raise NotImplementedError()

    @classmethod
    def set_system_text(cls, content):
        raise NotImplementedError()

    @classmethod
    def clear_clipboard(cls):
        raise NotImplementedError()

    def has_text(self):
        """ Determine whether this instance has text content. """
        raise NotImplementedError()

    def set_text(self, content):
        raise NotImplementedError()

    def get_text(self):
        raise NotImplementedError()


class Clipboard(BaseClipboard):
    """
    This class provides multi-platform clipboard support through pyperclip.

    The only currently supported Windows clipboard format is Unicode text.
    The Clipboard class in dragonfly.windows.clipboard can be used instead
    if required.
    """

    # ----------------------------------------------------------------------

    @classmethod
    def get_system_text(cls):
        return pyperclip.paste()

    @classmethod
    def set_system_text(cls, content):
        if not content:
            content = ""
        pyperclip.copy(content)

    @classmethod
    def clear_clipboard(cls):
        cls.set_system_text("")

    # ----------------------------------------------------------------------

    def __init__(self, contents=None, text=None, from_system=False):
        # Process given contents for this Clipboard instance
        content = contents
        if contents and isinstance(contents, dict):
            # Keep constructor arguments compatible with the Windows-only
            # clipboard class.
            format_unicode = 13
            format_text = 1
            unicode_content = contents.get(format_unicode, None)
            text_content = contents.get(format_text, None)
            if unicode_content:
                content = unicode_content
            elif text_content:
                content = text_content

        self._content = content

        # If requested, retrieve current system clipboard contents.
        if from_system:
            self.copy_from_system()

        # Handle text content.
        if text is not None:
            self._content = text_type(text)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self._content)

    def copy_from_system(self, clear=False):
        """
            Copy the system clipboard contents into this instance.

            Arguments:
             - *clear* (boolean, default: False) -- if true, the system
               clipboard will be cleared after its contents have been
               retrieved.

        """
        # Retrieve the system clipboard content.
        self._content = self.get_system_text()

        # Then clear the system clipboard, if requested.
        if clear:
            self.clear_clipboard()

    def copy_to_system(self):
        """
            Copy the contents of this instance into the system clipboard.
        """
        # Transfer content to system clipboard.
        self.set_system_text(self._content)

    def has_text(self):
        return bool(self._content)

    def get_text(self):
        """
            Retrieve this instance's text content.  If no text content
            is available, this method returns *None*.

        """
        return None if not self._content else self._content

    def set_text(self, content):
        self._content = text_type(content)

    text = property(get_text, set_text)
