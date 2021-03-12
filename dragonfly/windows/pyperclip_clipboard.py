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

# pylint: disable=W0622
# Suppress warnings about redefining the built-in 'format' function.

from six import integer_types
import pyperclip

from .base_clipboard import BaseClipboard


class PyperclipClipboard(BaseClipboard):
    """
    Class for interacting with the system clipboard via the
    `pyperclip <https://pyperclip.readthedocs.io/en/latest/>`__ Python
    package.

    This is Dragonfly's default clipboard class on platforms other than
    Windows.

    .. note::

       This class does work on Windows, however the Windows
       :class:`dragonfly.windows.win32_clipboard.Win32Clipboard` class
       should be used instead because this class doesn't support as many
       clipboard formats.

    """

    #-----------------------------------------------------------------------

    @classmethod
    def get_system_text(cls):
        return pyperclip.paste()

    @classmethod
    def set_system_text(cls, content):
        # If *content* is None, clear the clipboard and return early.
        if content is None:
            cls.clear_clipboard()
            return

        # Otherwise, convert *content* and set the system clipboard data.
        content = cls.convert_format_content(cls.format_unicode, content)
        pyperclip.copy(content)

    @classmethod
    def clear_clipboard(cls):
        cls.set_system_text(u"")

    # ----------------------------------------------------------------------

    def copy_from_system(self, formats=None, clear=False):
        # Determine which formats to retrieve.
        if not formats:
            formats = (self.format_text, self.format_unicode)
        elif isinstance(formats, integer_types):
            formats = (formats,)

        # Verify that the given formats are valid.
        for format in formats:
            if not isinstance(format, integer_types):
                raise TypeError("Invalid clipboard format: %r"
                                % format)

        # Retrieve the system clipboard content.
        # This class only handles text formats.
        text = self.get_system_text()
        contents = {}
        if self.format_text in formats:
            text = self.convert_format_content(self.format_text, text)
            contents[self.format_text] = text
        if self.format_unicode in formats:
            text = self.convert_format_content(self.format_unicode, text)
            contents[self.format_unicode] = text
        self._contents = contents

        # Then clear the system clipboard, if requested.
        if clear:
            self.clear_clipboard()

    def copy_to_system(self, clear=True):
        # Clear the system clipboard, if requested.
        if clear:
            self.clear_clipboard()

        # Transfer text content to system clipboard, if necessary.
        text = self.get_text()
        if text is not None:
            self.set_system_text(text)
