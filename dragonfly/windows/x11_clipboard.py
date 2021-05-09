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
This file implements interfaces to the X selections (clipboards):

 * Abstract BaseX11Clipboard interface to the X selections.
 * XselClipboard class implementation using the xsel program.

"""

# pylint: disable=W0622
# Suppress warnings about redefining the built-in 'format' function.

from __future__ import print_function

import locale
from subprocess import Popen, PIPE
import sys

from six import integer_types, binary_type

from .base_clipboard import BaseClipboard


#===========================================================================


class BaseX11Clipboard(BaseClipboard):
    """
    Base X11 clipboard class.
    """

    format_text      = 1
    format_unicode   = 13
    format_hdrop     = 15

    # Include formats for the standard three X selections.
    #: Format for the primary X selection.
    format_x_primary   = 0x10000

    #: Format for the secondary X selection.
    format_x_secondary = 0x10001

    #: Format for the clipboard X selection (alias of format_unicode).
    format_x_clipboard = 13

    format_names = {
        format_text:        "text",
        format_unicode:     "unicode",
        format_x_primary:   "x_primary",
        format_x_secondary: "x_secondary",
        format_hdrop:       "hdrop",
    }

    #-----------------------------------------------------------------------

    @classmethod
    def _get_x_selection(cls, format):
        raise NotImplementedError()

    @classmethod
    def _set_x_selection(cls, format, content):
        raise NotImplementedError()

    #-----------------------------------------------------------------------

    @classmethod
    def get_system_text(cls):
        try:
            return cls._get_x_selection(cls.format_x_clipboard)
        except TypeError:
            # Return the empty string if there is nothing in the selection
            #  or if its contents could not be retrieved.
            return u""

    @classmethod
    def set_system_text(cls, content):
        # If *content* is None, clear the clipboard and return early.
        if content is None:
            cls.clear_clipboard()
            return

        # Otherwise, convert *content* and set the system clipboard data.
        content = cls.convert_format_content(cls.format_unicode, content)
        cls._set_x_selection(cls.format_x_clipboard, content)

    @classmethod
    def clear_clipboard(cls):
        cls.set_system_text(u"")

    #-----------------------------------------------------------------------

    def copy_from_system(self, formats=None, clear=False):
        # pylint: disable=too-many-branches
        # Determine which formats to retrieve.
        supported_formats = (self.format_text, self.format_unicode,
                             self.format_hdrop, self.format_x_primary,
                             self.format_x_secondary)
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
        try:
            clipboard_text = self._get_x_selection(self.format_x_clipboard)
        except TypeError:
            clipboard_text = u""
        contents = {}

        # Populate the clipboard contents dictionary and raise errors for
        #  unavailable formats.
        for format in formats:
            err = False
            try:
                # Retrieve and use other X selections as text, if required.
                if format in (self.format_x_primary,
                              self.format_x_secondary):
                    text = self._get_x_selection(format)
                else:
                    text = clipboard_text

                # Attempt to convert and set text for this clipboard format.
                content = self.convert_format_content(format, text)
                contents[format] = content
            except (ValueError, TypeError):
                err = True

            # Do not raise errors for formats that the caller did not
            #  specify.
            if format in supported_formats and not caller_specified_formats:
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

        # Transfer content to the X selections.
        # Text content is put on the clipboard selection, if necessary.
        text = self.get_text()
        if text is not None:
            self._set_x_selection(self.format_x_clipboard, text)

        # CF_HDROP content is put on the clipboard selection, if necessary.
        #  This might not work properly.
        elif self.has_format(self.format_hdrop):
            file_paths = self.get_format(self.format_hdrop)
            content = u"\n".join(file_paths) + u"\n"
            self._set_x_selection(self.format_x_clipboard, content)

        # Set the primary selection content, if necessary.
        if self.has_format(self.format_x_primary):
            content = self.get_format(self.format_x_primary)
            self._set_x_selection(self.format_x_primary, content)

        # Set the secondary selection content, if necessary.
        if self.has_format(self.format_x_secondary):
            content = self.get_format(self.format_x_secondary)
            self._set_x_selection(self.format_x_secondary, content)


#===========================================================================


class XselClipboard(BaseX11Clipboard):
    """
    Class for interacting with X selections (clipboards) using xsel.

    This is Dragonfly's default clipboard class on X11/Linux.

    """

    @classmethod
    def _run_command(cls, command, arguments, input_data=None):
        """
        Run a command with arguments and return the result.
        """
        arguments = [str(arg) for arg in arguments]
        full_command = [command] + arguments
        full_readable_command = ' '.join(full_command)
        cls._log.debug(full_readable_command)
        try:
            # Execute the child process, passing input data if necessary.
            encoding = locale.getpreferredencoding()
            popen_kwargs = dict(stdout=PIPE, stderr=PIPE)
            comm_kwargs = {}
            if input_data is not None:
                popen_kwargs["stdin"] = PIPE
                if not isinstance(input_data, binary_type):
                    input_data = input_data.encode(encoding)
                comm_kwargs["input"] = input_data
            p = Popen(full_command, **popen_kwargs)
            stdout, stderr = p.communicate(**comm_kwargs)

            # Decode output if it is binary.
            if isinstance(stdout, binary_type):
                stdout = stdout.decode(encoding)
            if isinstance(stderr, binary_type):
                stderr = stderr.decode(encoding)

            # Print error messages to stderr.
            if stderr:
                print(stderr, file=sys.stderr)

            # Return the process output and return code.
            return stdout, p.returncode
        except OSError as e:
            cls._log.error("Failed to execute command '%s': %s. Is "
                           "%s installed?",
                           full_readable_command, e, command)
            raise e

    @classmethod
    def _get_x_selection(cls, format):
        if format == cls.format_x_primary:
            arguments = ["--primary", "-o"]
        elif format == cls.format_x_secondary:
            arguments = ["--secondary", "-o"]
        elif format == cls.format_x_clipboard:
            arguments = ["--clipboard", "-o"]
        else:
            raise ValueError("Invalid X selection: %r" % format)

        stdout, return_code = cls._run_command("xsel", arguments)
        if return_code != 0 or not stdout:
            format_repr = cls.format_names.get(format, format)
            message = ("Specified X selection %r is not available."
                       % format_repr)
            raise TypeError(message)

        return stdout

    @classmethod
    def _set_x_selection(cls, format, content):
        if format == cls.format_x_primary:
            arguments = ["--primary", "-i"]
        elif format == cls.format_x_secondary:
            arguments = ["--secondary", "-i"]
        elif format == cls.format_x_clipboard:
            arguments = ["--clipboard", "-i"]
        else:
            raise ValueError("Invalid X selection: %r" % format)
        _, return_code = cls._run_command("xsel", arguments, content)
        if return_code != 0:
            format_repr = cls.format_names.get(format, format)
            message = ("Specified X selection %r could not be set."
                       % format_repr)
            raise TypeError(message)
