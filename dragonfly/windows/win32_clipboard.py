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
This file implements an interface to the Windows system clipboard.
"""

# pylint: disable=E0401
# This file imports Win32-only modules.

# pylint: disable=W0622
# Suppress warnings about redefining the built-in 'format' function.

import contextlib
import locale
import time

from six import text_type, integer_types

import pywintypes
import win32clipboard
import win32con

from .base_clipboard import BaseClipboard

#===========================================================================


@contextlib.contextmanager
def win32_clipboard_ctx():
    """
    Python context manager for safely opening the Windows clipboard by
    polling for access for up to 500 ms.

    The polling is necessary because the clipboard is a shared resource
    which may be in use by another process.

    Use with a Python 'with' block::

       with win32_clipboard_ctx():
           # Do clipboard operation(s).
           win32clipboard.EmptyClipboard()

    """
    timeout = time.time() + 0.5
    success = False
    while time.time() < timeout:
        # Attempt to open the clipboard, catching Windows errors.
        try:
            win32clipboard.OpenClipboard()
            success = True
            break
        except pywintypes.error:
            # Failure. Try again in 10 ms.
            time.sleep(0.01)

    # Try opening the clipboard one more time if it still isn't open.
    # If this fails, then an error will be raised this time.
    if not success:
        win32clipboard.OpenClipboard()

    # The clipboard is open now, so yield and close the clipboard
    # afterwards.
    try:
        yield
    finally:
        win32clipboard.CloseClipboard()


class Win32Clipboard(BaseClipboard):
    """
    Class for interacting with the Windows system clipboard.

    This is Dragonfly's default clipboard class on Windows.

    """

    #-----------------------------------------------------------------------

    format_text      = win32con.CF_TEXT
    format_oemtext   = win32con.CF_OEMTEXT
    format_unicode   = win32con.CF_UNICODETEXT
    format_locale    = win32con.CF_LOCALE
    format_hdrop     = win32con.CF_HDROP
    format_names = {
        format_text:     "text",
        format_oemtext:  "oemtext",
        format_unicode:  "unicode",
        format_locale:   "locale",
        format_hdrop:    "hdrop",
    }

    @classmethod
    def get_system_text(cls):
        with win32_clipboard_ctx():
            try:
                content = win32clipboard.GetClipboardData(
                    cls.format_unicode)
                if not content:
                    content = win32clipboard.GetClipboardData(
                        cls.format_text)
            except (TypeError, pywintypes.error):
                content = u""
        return content

    @classmethod
    def set_system_text(cls, content):
        # If *content* is None, clear the clipboard and return early.
        if content is None:
            cls.clear_clipboard()
            return

        # Otherwise, convert *content* and set the system clipboard data.
        content = cls.convert_format_content(cls.format_unicode, content)
        with win32_clipboard_ctx():
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(cls.format_unicode, content)

    @classmethod
    def clear_clipboard(cls):
        with win32_clipboard_ctx():
            win32clipboard.EmptyClipboard()

    #-----------------------------------------------------------------------

    def _update_format_names(self, formats):
        # Retrieve and store the names of any registered clipboard formats
        #  in format_names, if necessary.
        for format in formats:
            if format in self.format_names:
                continue

            # Registered clipboard formats are identified by values in
            #  the range 0xC000 through 0xFFFF.
            if 0xC000 <= format <= 0xFFFF:
                format_name = win32clipboard.GetClipboardFormatName(format)
                self.format_names[format] = format_name

    def copy_from_system(self, formats=None, clear=False):
        with win32_clipboard_ctx():
            # Determine which formats to retrieve.
            caller_specified_formats = bool(formats)
            if not formats:
                format = 0
                formats = []
                while 1:
                    format = win32clipboard.EnumClipboardFormats(format)
                    if not format:
                        break
                    formats.append(format)
            elif isinstance(formats, integer_types):
                formats = (formats,)

            # Verify that the given formats are valid.
            for format in formats:
                if not isinstance(format, integer_types):
                    raise TypeError("Invalid clipboard format: %r"
                                    % format)

            # Update clipboard format names.
            self._update_format_names(formats)

            # Retrieve Windows system clipboard content.
            contents = {}
            for format in formats:
                # Allow GetClipboardData() to raise Windows API errors if
                #  the caller specified one or more formats.  If the
                #  function raises an error at this point, it is likely the
                #  format is not retrievable and the caller will want to
                #  know, since they explicitly asked for this format.
                if caller_specified_formats:
                    content = win32clipboard.GetClipboardData(format)
                    contents[format] = content
                    continue

                # Otherwise, catch and log Windows API errors.  We assume
                #  here that the caller is not much interested in
                #  irretrievable formats.
                try:
                    content = win32clipboard.GetClipboardData(format)
                    contents[format] = content
                except pywintypes.error as err:
                    format_repr = self.format_names.get(format, format)
                    self._log.warning("Could not retrieve clipboard data "
                                      "for format %r: %s", format_repr, err)

            self._contents = contents

            # Clear the system clipboard, if requested, and close it.
            if clear:
                win32clipboard.EmptyClipboard()

    def copy_to_system(self, clear=True):
        with win32_clipboard_ctx():
            # Clear the system clipboard, if requested.
            if clear:
                win32clipboard.EmptyClipboard()

            # Transfer content to Windows system clipboard.
            for format, content in self._contents.items():
                win32clipboard.SetClipboardData(format, content)
