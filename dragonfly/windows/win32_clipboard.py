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
import logging
import sys
import time
import threading

from six import integer_types, reraise

import pywintypes
import win32clipboard
import win32con

from .base_clipboard import BaseClipboard

#===========================================================================

class win32_clipboard_ctx(object):
    """
    Python context manager for safely opening the Windows clipboard by
    polling for access, timing out after the specified number of seconds.

    Arguments:
     - *timeout* (float, default: 0.5) -- timeout in seconds.
     - *step* (float, default: 0.001) -- number of seconds between each
       attempt to open the clipboard.

    Notes:
     - The polling is necessary because the clipboard is a shared resource
       which may be in use by another process.
     - Nested usage will not close the clipboard early.

    Use with a Python 'with' block::

       with win32_clipboard_ctx():
           # Do clipboard operation(s).
           win32clipboard.EmptyClipboard()

    """

    _ctx_data = threading.local()
    _log = logging.getLogger("clipboard")

    def __init__(self, timeout=0.5, step=0.001):
        self._timeout = float(timeout)
        self._step = float(step)

    def __enter__(self):
        timeout = time.time() + self._timeout
        success = False
        while time.time() < timeout:
            # Attempt to open the clipboard, catching Windows errors.
            try:
                win32clipboard.OpenClipboard()
                success = True
                break
            except pywintypes.error:
                # Failure. Try again after *step* seconds.
                time.sleep(self._step)

        # Try opening the clipboard one more time if it still isn't open.
        #  If this fails, then an error will be raised this time.
        if not success:
            win32clipboard.OpenClipboard()

        # The clipboard is open now.  Increment our thread-local counter to
        #  keep track of nested usage.
        ctx_data = self._ctx_data
        ctx_data.count = getattr(ctx_data, "count", 0) + 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        # The clipboard is (presumably) still open.  Decrement our thread-
        #  local counter and close the clipboard if it is at 0 again.
        ctx_data = self._ctx_data
        ctx_data.count -= 1
        if ctx_data.count == 0:
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

    @classmethod
    def _wait_for_change(cls, timeout, step, formats, initial_clipboard,
                         seq_no):
        # This method determines if the system clipboard has changed by
        #  repeatedly checking the current sequence number.  Contents are
        #  compared if specific clipboard formats are given.
        timeout = time.time() + float(timeout)
        step = float(step)
        if isinstance(formats, integer_types):
            formats = (formats,)
        elif formats:
            for format in formats:
                if not isinstance(format, integer_types):
                    raise TypeError("Invalid clipboard format: %r"
                                    % format)
        clipboard2 = cls() if formats or initial_clipboard else None
        result = False
        while time.time() < timeout:
            seq_no_change = (win32clipboard.GetClipboardSequenceNumber()
                             != seq_no)
            if seq_no_change and initial_clipboard:
                # Check if the content of any relevant format has changed.
                clipboard2.copy_from_system()
                formats_to_compare = formats if formats else "all"
                result = cls._clipboard_formats_changed(formats_to_compare,
                                                        initial_clipboard,
                                                        clipboard2)

                # Reset the sequence number if the clipboard change is not
                #  related.
                if not result:
                    seq_no = win32clipboard.GetClipboardSequenceNumber()
            elif seq_no_change:
                result = True

            if result:
                break

            # Failure. Try again after *step* seconds.
            time.sleep(step)
        return result

    @classmethod
    def wait_for_change(cls, timeout, step=0.001, formats=None,
                        initial_clipboard=None):
        # Save the current clipboard sequence number and clipboard contents,
        #  as necessary. The latter is not required unless formats are
        #  specified.
        seq_no = win32clipboard.GetClipboardSequenceNumber()
        if formats and not initial_clipboard:
            initial_clipboard = cls(from_system=True)
        return cls._wait_for_change(timeout, step, formats,
                                    initial_clipboard, seq_no)

    @classmethod
    @contextlib.contextmanager
    def synchronized_changes(cls, timeout, step=0.001, formats=None,
                             initial_clipboard=None):
        seq_no = win32clipboard.GetClipboardSequenceNumber()
        if formats and not initial_clipboard:
            initial_clipboard = cls(from_system=True)
        try:
            # Yield for clipboard operations.
            yield
        finally:
            # Wait for the system clipboard to change.
            cls._wait_for_change(timeout, step, formats, initial_clipboard,
                                 seq_no)

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
