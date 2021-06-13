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
This file contains the base interface to the system clipboard.
"""

# pylint: disable=W0622
# Suppress warnings about redefining the built-in 'format' function.

import contextlib
import functools
import locale
import logging
import os
import re
import time

from six import text_type, binary_type, integer_types


#===========================================================================


@functools.total_ordering
class BaseClipboard(object):
    """
    Base clipboard class.
    """

    _log = logging.getLogger("clipboard")

    format_text      = 1
    format_unicode   = 13
    format_hdrop     = 15
    format_names = {
        format_text:     "text",
        format_unicode:  "unicode",
        format_hdrop:    "hdrop",
    }

    #-----------------------------------------------------------------------

    @classmethod
    def get_system_text(cls):
        """
        Retrieve the system clipboard text.
        """
        raise NotImplementedError()

    @classmethod
    def set_system_text(cls, content):
        """
            Set the system clipboard text.

            Arguments:
             - *content* (string) -- the clipboard contents to set.

            If *None* is given as the *content*, text on the system
            clipboard will be cleared.

        """
        raise NotImplementedError()

    @classmethod
    def clear_clipboard(cls):
        """
        Clear the system clipboard.
        """
        raise NotImplementedError()

    @classmethod
    def _clipboard_formats_changed(cls, formats, clipboard1, clipboard2):
        # Check if the content of any specified format has changed.
        # Use all formats, if specified.
        if formats == "all":
            return clipboard1 != clipboard2
        result = False
        for format in formats:
            format_available = clipboard1.has_format(format)
            result = (
                format_available != clipboard2.has_format(format) or
                format_available and clipboard1.get_format(format)
                != clipboard2.get_format(format))
            if result:
                break
        return result

    @classmethod
    def wait_for_change(cls, timeout, step=0.001, formats=None,
                        initial_clipboard=None):
        """
            Wait (poll) for the system clipboard to change.

            This is a blocking method which returns whether or not the
            system clipboard changed within a specified timeout period.

            Arguments:
             - *timeout* (float) -- timeout in seconds.
             - *step* (float, default: 0.001) -- number of seconds between
               each check.
             - *formats* (iterable, default: None) -- if not None, only
               changes to the given content formats will register.  If None,
               all formats will be observed.
             - *initial_clipboard* (Clipboard, default: None) -- if a
               clipboard is given, the method will wait until the system
               clipboard differs from the instance's contents.

        """
        # By default, this method retrieves the system clipboard every
        #  *step* seconds until the contents change.  This method should be
        #  overridden by the sub-class if there is a more efficient way for
        #  the platform.
        if not initial_clipboard:
            initial_clipboard = cls(from_system=True)
        clipboard2 = cls()
        timeout = time.time() + float(timeout)
        step = float(step)
        if isinstance(formats, integer_types):
            formats = (formats,)
        elif formats:
            for format in formats:
                if not isinstance(format, integer_types):
                    raise TypeError("Invalid clipboard format: %r"
                                    % format)
        result = False
        while time.time() < timeout:
            # Check if the content of any relevant format has changed.
            clipboard2.copy_from_system()
            formats_to_compare = formats if formats else "all"
            result = cls._clipboard_formats_changed(formats_to_compare,
                                                    initial_clipboard,
                                                    clipboard2)

            if result:
                break

            # Failure. Try again after *step* seconds.
            time.sleep(step)
        return result

    @classmethod
    @contextlib.contextmanager
    def synchronized_changes(cls, timeout, step=0.001, formats=None,
                             initial_clipboard=None):
        """
            Context manager for synchronizing local and system clipboard
            changes.  This takes the same arguments as the
            :meth:`wait_for_change` method.

            Arguments:
             - *timeout* (float) -- timeout in seconds.
             - *step* (float, default: 0.001) -- number of seconds between
               each check.
             - *formats* (iterable, default: None) -- if not None, only
               changes to the given content formats will register.  If None,
               all formats will be observed.
             - *initial_clipboard* (Clipboard, default: None) -- if a
               clipboard is given, the method will wait until the system
               clipboard differs from the instance's contents.

            Use with a Python 'with' block::

               from dragonfly import Clipboard, Key

               # Copy the selected text with Ctrl+C and wait until a system
               #  clipboard change is detected.
               timeout = 3
               with Clipboard.synchronized_changes(timeout):
                   Key("c-c", use_hardware=True).execute()

               # Retrieve the system text.
               text = Clipboard.get_system_text()

        """
        # Save the current clipboard contents, if necessary.
        if initial_clipboard:
            initial_clipboard = cls(from_system=True)
        try:
            # Yield for clipboard operations.
            yield
        finally:
            # Wait for the system clipboard to change.
            cls.wait_for_change(timeout, step, formats, initial_clipboard)

    #-----------------------------------------------------------------------

    @classmethod
    def _convert_format_text(cls, content):
        format_name = cls.format_names[cls.format_text]
        if not isinstance(content, (text_type, binary_type)):
            raise TypeError("Invalid content for format %s: (%r)"
                            % (format_name, content,))

        # Use a binary string for CF_TEXT content.
        if isinstance(content, text_type):
            encoding = locale.getpreferredencoding()
            content = content.encode(encoding)

        return content

    @classmethod
    def _convert_format_unicode(cls, content):
        format_name = cls.format_names[cls.format_unicode]
        if not isinstance(content, (text_type, binary_type)):
            raise TypeError("Invalid content for format %s: (%r)"
                            % (format_name, content,))

        # Use a text string for CF_UNICODETEXT content.
        if isinstance(content, binary_type):
            encoding = locale.getpreferredencoding()
            content = content.decode(encoding)

        return content

    @classmethod
    def _convert_format_hdrop(cls, content):
        # The CF_HDROP clipboard format is for copied file paths.
        format_name = cls.format_names[cls.format_hdrop]
        result = content

        # Convert string content into a list of file paths.  String content
        #  must be a list of file paths separated by new lines and/or null
        #  characters.  The following example string is acceptable:
        #  "c:\\temp1.txt\0c:\\temp2.txt\0\0".
        if isinstance(content, (text_type, binary_type)):
            delimiter = u"[\0\r\n]"
            if isinstance(content, binary_type):
                delimiter = delimiter.encode()

            # Convert string content into a list and remove empty
            #  strings.
            result = re.split(delimiter, content)
            result = [string for string in result if string]

        # Verify that the list/tuple items are non-empty strings.
        elif isinstance(content, (list, tuple)):
            string_items = all([
                isinstance(item, (text_type, binary_type)) and item
                for item in content
            ])
            if not string_items:
                raise TypeError("Invalid content type for format %s: (%r)"
                                % (format_name, content))

        # Only strings, tuples and lists are accepted for CF_HDROP
        #  content.
        else:
            raise TypeError("Invalid content type for format %s: (%r)"
                            % (format_name, content))

        # Remove the file scheme from strings if it is present.
        file_paths = []
        for string in result:
            file_scheme = (u"file://" if isinstance(string, text_type)
                           else b"file://")
            if string.startswith(file_scheme):
                string = string[7:]
            file_paths.append(string)
        result = file_paths

        # Empty lists/tuples are not acceptable.
        if not result:
            raise ValueError("Invalid content value for format %s: (%r)"
                             % (format_name, content))

        # Verify that strings in the content list are existing, absolute
        #  file paths.  Relative paths are not accepted because they do not
        #  make sense without the context of a working directory. The system
        #  clipboard does not typically have such a context.
        file_paths_exist = all([
            os.path.isabs(item) and os.path.exists(item)
            for item in result
        ])
        if not (file_paths_exist and result):
            raise ValueError("Invalid content value for format %s: (%r)"
                             % (format_name, content))

        # Use a tuple for CF_HDROP content.
        if isinstance(result, list):
            result = tuple(result)

        return result

    @classmethod
    def convert_format_content(cls, format, content):
        """
            Convert content for the given *format*, if necessary, and return
            it.

            This method operates on the following formats:
             - *text* -- encodes content to a binary string, if necessary
               and if possible.
             - *unicode* -- decodes content to a text string, if necessary
               and if possible.
             - *hdrop* -- converts content into a tuple of file paths, if
               necessary and if possible.

               String content must be a list of existing, absolute file
               paths separated by new lines and/or null characters.  All
               specified file paths must be absolute paths referring to
               existing files on the system.

            If the content cannot be converted for the given *format*, an
            error is raised.

            Arguments:
             - *format* (int) -- the clipboard format to convert.
             - *content* (string) -- the clipboard contents to convert.

        """
        convert_method = {
            cls.format_text:     cls._convert_format_text,
            cls.format_unicode:  cls._convert_format_unicode,
            cls.format_hdrop:    cls._convert_format_hdrop,
        }.get(format)
        if convert_method is not None:
            content = convert_method(content)

        # Return the content.
        return content

    #-----------------------------------------------------------------------

    def __init__(self, contents=None, text=None, from_system=False):
        self._contents = {}

        # If requested, retrieve current system clipboard contents.
        if from_system:
            self.copy_from_system()

        # Process given contents for this Clipboard instance.
        if contents:
            try:
                contents = dict(contents)

                # Enumerate and add contents, converting contents if
                #  necessary.
                for format, content in contents.items():
                    content = self.convert_format_content(format, content)
                    self._contents[format] = content
            except Exception as e:
                raise TypeError("Invalid contents: %s (%r)" % (e, contents))

        # Handle special case of text content.
        if text is not None:
            text = self.convert_format_content(self.format_unicode, text)
            self._contents[self.format_unicode] = text

    def __eq__(self, other):
        formats = self.get_available_formats()
        if formats != other.get_available_formats():
            return False
        for format in formats:
            if self.get_format(format) != other.get_format(format):
                return False
        return True

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        return not self == other

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
            Copy the system clipboard contents into this instance.

            Arguments:
             - *formats* (iterable, default: None) -- if not None, only the
               given content formats will be retrieved.  If None, all
               available formats will be retrieved.
             - *clear* (boolean, default: False) -- if true, the system
               clipboard will be cleared after its contents have been
               retrieved.

        """
        raise NotImplementedError()

    def copy_to_system(self, clear=True):
        """
            Copy the contents of this instance into the system clipboard.

            Arguments:
             - *clear* (boolean, default: True) -- if true, the system
               clipboard will be cleared before this instance's contents are
               transferred.

        """
        raise NotImplementedError()

    def get_available_formats(self):
        """
            Retrieve a list of this instance's available formats.

            The preferred text format, if available, will always be the
            first on the list followed by any remaining formats in
            numerical order.

        """
        # Return a list of available formats using the same order as
        #  __repr__().
        formats = []
        if self.format_unicode in self._contents:
            formats.append(self.format_unicode)
        elif self.format_text in self._contents:
            formats.append(self.format_text)
        for format in sorted(self._contents.keys()):
            if format in formats:
                continue
            formats.append(format)

        return formats

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

            If *None* is given as the *content*, any content stored
            for the given *format* will be cleared.
        """
        if content is None:
            self._contents.pop(format, None)
        else:
            content = self.convert_format_content(format, content)
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
        """
            Set the text content for this instance.

            Arguments:
             - *content* (string) -- the text content to set.

            If *None* is given as the *content*, any text content
            stored in this instance will be cleared.

        """
        # Clear text content for this instance, if requested.
        if content is None:
            self._contents.pop(self.format_text, None)
            self._contents.pop(self.format_unicode, None)
            return

        if isinstance(content, binary_type):
            format = self.format_text
        else:
            format = self.format_unicode

        # Set this instance's content for the appropriate format.
        self.set_format(format, content)

    text = property(get_text, set_text)
