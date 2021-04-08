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

import os

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
        # Determine the supported formats.  Copied file paths may be
        #  available to us on X11.
        supported_formats = [self.format_text, self.format_unicode]
        if os.environ.get("XDG_SESSION_TYPE") == "x11":
            supported_formats.append(self.format_hdrop)

        # Determine which formats to retrieve.
        caller_specified_formats = bool(formats)
        if not formats:
            formats = supported_formats
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

        # Populate the clipboard contents dictionary and raise errors for
        #  unavailable formats.
        for format in formats:
            try:
                err = False
                content = self.convert_format_content(format, text)
                contents[format] = content
            except (ValueError, TypeError):
                err = True

            # Do not raise an error for CF_HDROP content if the caller did
            #  not specify it.
            if format == self.format_hdrop and not caller_specified_formats:
                err = False

            # Always raise an error if the format is not supported.
            if format not in supported_formats:
                err = True

            # Raise an error if a specified clipboard format was not
            #  available.
            if err:
                format_repr = self.format_names.get(format, format)
                message = ("Specified clipboard format %r is not "
                           "available." % format_repr)
                raise TypeError(message)
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
