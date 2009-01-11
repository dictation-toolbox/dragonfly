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
This file implements an edit control which can be used as a Python stream
for text-based output.  It can for example be assigned to standard
output and standard error to display Python print statements and
exception trace back.

"""


#---------------------------------------------------------------------------

import sys
import win32con

from dragonfly.windows.control_base import ControlBase


#---------------------------------------------------------------------------

class OutputText(ControlBase):

    def __init__(self, parent, size, **kwargs):
        flavor = "EDIT"
        text = ""
        style = ( win32con.WS_CHILD
                | win32con.WS_VISIBLE
                | win32con.ES_LEFT
                | win32con.ES_MULTILINE
                | win32con.ES_AUTOVSCROLL
                | win32con.WS_TABSTOP
                | win32con.WS_BORDER
                | win32con.ES_READONLY
                | win32con.WS_VSCROLL)
        ControlBase.__init__(self, parent, flavor, text, size, style, **kwargs)

    def set_as_output(self):
        self._old_stdout = sys.stdout
        self._old_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self

    def write(self, data):
        length = win32gui.GetWindowTextLength(self.handle)
        win32gui.SendMessage(self.handle, win32con.EM_SETSEL, length, length)
        win32gui.SendMessage(self.handle, win32con.EM_REPLACESEL, False, data)

    def flush(self):
        pass
