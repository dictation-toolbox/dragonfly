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

import locale
import logging

from six import text_type, binary_type


#===========================================================================


class BaseClipboard(object):
    """
    Base clipboard class.
    """

    _log = logging.getLogger("clipboard")

    format_text      = 1
    format_unicode   = 13
    format_names = {
        format_text:     "text",
        format_unicode:  "unicode",
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
    def convert_format_content(cls, format, content):
        """
            Convert content for the given *format*, if necessary, and return
            it.

            This method operates on the following formats:
             - *text* -- encodes content to a binary string, if necessary
               and if possible.
             - *unicode* -- decodes content to a text string, if necessary
               and if possible.

            If the content cannot be converted for the given *format*, an
            error is raised.

            Arguments:
             - *format* (int) -- the clipboard format to convert.
             - *content* (string) -- the clipboard contents to convert.

        """
        if format in (cls.format_text, cls.format_unicode):
            if not isinstance(content, (text_type, binary_type)):
                raise TypeError("Invalid content for format %s: (%r)"
                                % (cls.format_names[format], content))

            # Use a binary string for CF_TEXT content.
            if format == cls.format_text and isinstance(content, text_type):
                encoding = locale.getpreferredencoding()
                content = content.encode(encoding)

            # Use a text string for CF_UNICODETEXT content.
            elif (format == cls.format_unicode and isinstance(content,
                                                              binary_type)):
                encoding = locale.getpreferredencoding()
                content = content.decode(encoding)

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
