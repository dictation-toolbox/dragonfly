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
This file implements a standard Win32 button control.

"""


#---------------------------------------------------------------------------

import win32con

from dragonfly.windows.control_base import ControlBase


#---------------------------------------------------------------------------

class Button(ControlBase):

    def __init__(self, parent, text, size, default=False, **kwargs):
        flavor = 128
        style =  ( win32con.BS_PUSHBUTTON
                 | win32con.BS_TEXT
                 | win32con.WS_CHILD
                 | win32con.WS_TABSTOP
                 | win32con.WS_OVERLAPPED
                 | win32con.WS_VISIBLE)
        if default:  style |= win32con.BS_DEFPUSHBUTTON
        else:        style |= win32con.BS_PUSHBUTTON
        ControlBase.__init__(self, parent, flavor, text, size, style,
                             **kwargs)
