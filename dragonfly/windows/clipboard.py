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


import win32clipboard
import win32con


#===========================================================================

class Clipboard(object):

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
        win32clipboard.OpenClipboard()
        try:
            content = win32clipboard.GetClipboardData(cls.format_unicode)
        finally:
            win32clipboard.CloseClipboard()
        return content

    @classmethod
    def set_system_text(cls, content):
        content = unicode(content)
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(cls.format_unicode, content)
        finally:
            win32clipboard.CloseClipboard()


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
            except Exception, e:
                raise TypeError("Invalid contents: %s (%r)" % (e, contents))

        # Handle special case of text content.
        if not text is None:
            self._contents[self.format_unicode] = unicode(text)

    def __str__(self):
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
        win32clipboard.OpenClipboard()

        # Determine which formats to retrieve.
        if not formats:
            format = 0
            formats = []
            while 1:
                format = win32clipboard.EnumClipboardFormats(format)
                if not format:
                    break
                formats.append(format)
        elif isinstance(formats, int):
            formats = (formats,)

        # Verify that the given formats are valid.
        try:
            for format in formats:
                if not isinstance(format, int):
                    raise TypeError("Invalid clipboard format: %r"
                                    % format)
        except Exception, e:
            raise

        # Retrieve Windows system clipboard content.
        contents = {}
        for format in formats:
            content = win32clipboard.GetClipboardData(format)
            contents[format] = content
        self._contents = contents

        # Clear the system clipboard, if requested, and close it.
        if clear:
            win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()

    def copy_to_system(self, clear=True):
        """
            Copy the contents of this instance into the Windows system
            clipboard.

            Arguments:
             - *clear* (boolean, default: True) -- if true, the Windows
               system clipboard will be cleared before this instance's
               contents are transferred.

        """
        win32clipboard.OpenClipboard()

        # Clear the system clipboard, if requested.
        if clear:
            win32clipboard.EmptyClipboard()

        # Transfer content to Windows system clipboard.
        for format, content in self._contents.items():
            win32clipboard.SetClipboardData(format, content)

        win32clipboard.CloseClipboard()

    def has_format(self, format):
        """
            Determine whether this instance has content for the given
            *format*.

            Arguments:
             - *format* (int) -- the clipboard format to look for.

        """
        return (format in self._contents)

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
        self._contents[self.format_unicode] = unicode(content)

    text    = property(
                       lambda self:    self.get_text(),
                       lambda self, d: self.set_text(d)
                      )
