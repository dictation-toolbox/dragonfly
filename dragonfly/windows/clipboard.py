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


import win32clipboard
import win32con


#===========================================================================

class Clipboard(object):

    #-----------------------------------------------------------------------
    # Class methods for manipulating the clipboard contents.

    @classmethod
    def get_text(cls):
        win32clipboard.OpenClipboard()
        content = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
        return content

    @classmethod
    def set_text(cls, content):
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        content = unicode(content)
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, content)
        win32clipboard.CloseClipboard()

    @classmethod
    def get_available_formats(cls):
        """
            Retrieve the list of formats available from the 
            Windows clipboard.

        """
        win32clipboard.OpenClipboard()
        format = 0
        formats = []
        while 1:
            format = win32clipboard.EnumClipboardFormats(format)
            if not format:
                break
            formats.append(format)
        win32clipboard.CloseClipboard()
        return formats

    #-----------------------------------------------------------------------

    def __init__(self, content=None, format=None):
        self.content = content
        self.format = format

    def __str__(self):
        return "%s(%r)" % (self.__class__.__name__, self.content)

    def get(self, format=win32con.CF_UNICODETEXT):
        """ Copy the Windows clipboard content into this instance. """
        win32clipboard.OpenClipboard()
        content = win32clipboard.GetClipboardData(format)
        win32clipboard.CloseClipboard()
        self.format = format
        self.content = content

    def set(self):
        """ Copy this instance's content into the Windows clipboard. """
        if self.content is None or self.format is None:
            raise ValueError("Cannot set clipboard with content"
                             " and/or format undefined.")
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        handle = win32clipboard.SetClipboardData(self.format, self.content)
        win32clipboard.CloseClipboard()

        if not handle:
            raise ValueError("Failed to set clipboard with content"
                             " %r." % self.content)
