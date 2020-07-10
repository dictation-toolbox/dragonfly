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

from ..util import BaseClipboard

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


class Clipboard(BaseClipboard):
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
        content = text_type(content)
        with win32_clipboard_ctx():
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(cls.format_unicode, content)

    @classmethod
    def clear_clipboard(cls):
        with win32_clipboard_ctx():
            win32clipboard.EmptyClipboard()

    #-----------------------------------------------------------------------

    def __init__(self, contents=None, text=None, from_system=False):
        self._contents = {}

        # If requested, retrieve current system clipboard contents.
        if from_system:
            self.copy_from_system()

        # Process given contents for this Clipboard instance.
        if contents:
            try:
                self._contents = dict(contents)
            except Exception as e:
                raise TypeError("Invalid contents: %s (%r)" % (e, contents))

        # Handle special case of text content.
        if not text is None:
            self._contents[self.format_unicode] = text_type(text)

        # Use a binary string for CF_TEXT content.
        cf_text_content = self._contents.get(self.format_text)
        if isinstance(cf_text_content, text_type):
            enc = locale.getpreferredencoding()
            self._contents[self.format_text] = cf_text_content.encode(enc)

    def __repr__(self):
        arguments = []
        skip = []
        if self.format_unicode in self._contents:
            arguments.append("unicode=%r"
                             % self._contents[self.format_unicode])
            skip.append(self.format_unicode)
        elif self.format_text in self._contents:
            arguments.append("text=%r" % self._contents[self.format_text])
            skip.append(self.format_text)
        for format in sorted(self._contents.keys()):
            if format in skip:
                continue
            if format in self.format_names:
                arguments.append(self.format_names[format])
            else:
                arguments.append(repr(format))
        arguments = ", ".join(str(a) for a in arguments)
        return "%s(%s)" % (self.__class__.__name__, arguments)

    def copy_from_system(self, formats=None, clear=False):
        """
            Copy the Windows system clipboard contents into this instance.

            Arguments:
             - *formats* (iterable, default: None) -- if not None, only the
               given content formats will be retrieved.  If None, all
               available formats will be retrieved.
             - *clear* (boolean, default: False) -- if true, the Windows
               system clipboard will be cleared after its contents have been
               retrieved.

        """
        with win32_clipboard_ctx():
            # Determine which formats to retrieve.
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

            # Retrieve Windows system clipboard content.
            contents = {}
            for format in formats:
                content = win32clipboard.GetClipboardData(format)
                contents[format] = content
            self._contents = contents

            # Clear the system clipboard, if requested, and close it.
            if clear:
                win32clipboard.EmptyClipboard()

    def copy_to_system(self, clear=True):
        """
            Copy the contents of this instance into the Windows system
            clipboard.

            Arguments:
             - *clear* (boolean, default: True) -- if true, the Windows
               system clipboard will be cleared before this instance's
               contents are transferred.

        """
        with win32_clipboard_ctx():
            # Clear the system clipboard, if requested.
            if clear:
                win32clipboard.EmptyClipboard()

            # Transfer content to Windows system clipboard.
            for format, content in self._contents.items():
                win32clipboard.SetClipboardData(format, content)

    def has_format(self, format):
        """
            Determine whether this instance has content for the given
            *format*.

            Arguments:
             - *format* (int) -- the clipboard format to look for.

        """
        return format in self._contents

    def get_format(self, format):
        """
            Retrieved this instance's content for the given *format*.

            Arguments:
             - *format* (int) -- the clipboard format to retrieve.

            If the given *format* is not available, a *ValueError*
            is raised.

        """
        try:
            return self._contents[format]
        except KeyError:
            raise ValueError("Clipboard format not available: %r"
                             % format)

    def set_format(self, format, content):
        """
            Set this instance's content for the given *format*.

            Arguments:
             - *format* (int) -- the clipboard format to set.
             - *content* (string) -- the clipboard contents to set.

            If the given *format* is not available, a *ValueError*
            is raised.
        """
        self._contents[format] = content

    def has_text(self):
        """ Determine whether this instance has text content. """
        return (self.format_unicode in self._contents
                or self.format_text in self._contents)

    def get_text(self):
        """
            Retrieve this instance's text content.  If no text content
            is available, this method returns *None*.

        """
        if self.format_unicode in self._contents:
            return self._contents[self.format_unicode]
        elif self.format_text in self._contents:
            return self._contents[self.format_text]
        else:
            return None

    def set_text(self, content):
        self._contents[self.format_unicode] = text_type(content)

    text = property(get_text, set_text)
