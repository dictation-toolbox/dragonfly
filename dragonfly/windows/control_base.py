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
This file implements a Win32 control base class.
"""


#---------------------------------------------------------------------------

import sys
import ctypes
import struct
import winxpgui as win32gui
import win32api
import win32con
import os


#---------------------------------------------------------------------------

class ControlBase(object):


    #-----------------------------------------------------------------------

    _next_id = 1024

    @classmethod
    def _get_next_id(cls):
        ControlBase._next_id += 1
        return ControlBase._next_id - 1

    _message_names = {
                      "on_command":      win32con.WM_COMMAND,
                     }


    #-----------------------------------------------------------------------

    def __init__(self, parent, flavor, text, size, style, **kwargs):
        self._parent = parent
        self._flavor = flavor
        self._text = text
        self._size = size
        self._style = style

        # Build this control's message callback mapping.
        self._message_callbacks = {}
        for name, callback in kwargs.items():
            message = self._message_names[name]
            self._message_callbacks[message] = callback

        # Get a control ID and register this control with its parent.
        self._id = self._get_next_id()
        self._handle = None
        self._parent.add_control(self)


    #-----------------------------------------------------------------------

    def _get_handle(self):
        if self._handle is not None:
            return self._handle
        self._handle = win32gui.GetDlgItem(self._parent.hwnd, self.id)
        return self._handle

    handle = property(lambda self: self._get_handle())


    #-----------------------------------------------------------------------

    def _get_text(self):
        return win32gui.GetWindowText(self.handle)

    def _set_text(self, text):
        return win32gui.SetWindowText(self.handle, text)

    text = property(
                    fget=lambda self: self._get_text(),
                    fset=lambda self, text: self._set_text(text),
                   )


    #-----------------------------------------------------------------------

    id                 = property(lambda self: self._id)
    message_callbacks  = property(lambda self: self._message_callbacks)


    #-----------------------------------------------------------------------

    def calculate_size(self, width, height):
        return self._size(width, height)

    def template_entry(self, width, height):
        entry = [self._flavor, self._text, self._id,
                 self.calculate_size(width, height), self._style]
        return entry

    def enable(self):
        style = win32gui.GetWindowLong(self.handle, win32con.GWL_STYLE)
        style &= (~win32con.WS_DISABLED)
        win32gui.SetWindowLong(self.handle, win32con.GWL_STYLE, style)
        win32gui.SendMessage(self.handle, win32con.WM_ENABLE, 1, 0)

    def disable(self):
        style = win32gui.GetWindowLong(self.handle, win32con.GWL_STYLE)
        style |= win32con.WS_DISABLED
        win32gui.SetWindowLong(self.handle, win32con.GWL_STYLE, style)
        win32gui.SendMessage(self.handle, win32con.WM_ENABLE, 0, 0)
