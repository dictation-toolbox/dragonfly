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
    This file implements a Window class as an interface to the Win32
    window control and placement.
"""


import win32gui
import win32con
from ctypes      import windll, pointer, c_wchar, c_ulong
from .rectangle  import Rectangle, unit
from .monitor    import monitors


#===========================================================================

class Window(object):

    #-----------------------------------------------------------------------
    # Class attributes to retrieve existing Window objects.

    _windows_by_name = {}
    _windows_by_handle = {}

    #-----------------------------------------------------------------------
    # Class methods to create new Window objects.

    @classmethod
    def get_foreground(cls):
        handle = win32gui.GetForegroundWindow()
        if handle in cls._windows_by_handle:
            return cls._windows_by_handle[handle]
        window = Window(handle=handle)
        return window

    @classmethod
    def get_all_windows(cls):
        def function(handle, argument):
            argument.append(Window(handle))
        argument = []
        win32gui.EnumWindows(function, argument)
        return argument

#    @classmethod
#    def get_window_by_executable(cls, executable):
#        def function(handle, argument):
#            title = windll.user32.GetWindowText(handle)
#            print "title: %r" % title
#        windll.user32.EnumWindows(function, argument)


    #=======================================================================
    # Methods for initialization and introspection.

    def __init__(self, handle):
        self._handle = None
        self._names = set()
        self.handle = handle

    def __str__(self):
        args = ["handle=%d" % self._handle] + list(self._names)
        return "%s(%s)" % (self.__class__.__name__, ", ".join(args))

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    def _set_handle(self, handle):
        assert isinstance(handle, int)
        self._handle = handle
        self._windows_by_handle[handle] = self
    handle = property(fget=lambda self: self._handle,
                      fset=_set_handle,
                      doc="Protected access to handle attribute.")

    def _get_name(self):
        if not self._names:
            return None
        for name in self._names:
            return name
    def _set_name(self, name):
        assert isinstance(name, basestring)
        self._names.add(name)
        self._windows_by_name[name] = self
    name = property(fget=_get_name,
                    fset=_set_name,
                    doc="Protected access to name attribute.")

    #-----------------------------------------------------------------------
    # Direct access to various Win32 methods.

    def _win32gui_func(name):
        func = getattr(win32gui, name)
        return lambda self: func(self._handle)

    _get_rect           = _win32gui_func("GetWindowRect")
    _destroy            = _win32gui_func("DestroyWindow")
    _set_foreground     = _win32gui_func("SetForegroundWindow")
    _bring_to_top       = _win32gui_func("BringWindowToTop")
    _get_window_text    = _win32gui_func("GetWindowText")
    _get_class_name     = _win32gui_func("GetClassName")

    title               = property(fget=_get_window_text)
    classname           = property(fget=_get_class_name)


    def _win32gui_test(name):
        test = getattr(win32gui, name)
        fget = lambda self: test(self._handle) and True or False
        return property(fget=fget,
                        doc="Shortcut to win32gui.%s() function." % name)

    is_valid        = _win32gui_test("IsWindow")
    is_enabled      = _win32gui_test("IsWindowEnabled")
    is_visible      = _win32gui_test("IsWindowVisible")
    is_minimized    = _win32gui_test("IsIconic")
#   is_maximized    = _win32gui_test("IsZoomed")


    def _win32gui_show_window(state):
        return lambda self: win32gui.ShowWindow(self._handle, state)

    minimize        = _win32gui_show_window(win32con.SW_MINIMIZE)
    maximize        = _win32gui_show_window(win32con.SW_MAXIMIZE)
    restore         = _win32gui_show_window(win32con.SW_RESTORE)


    def _get_window_module(self):
        # Get this window's process ID.
        pid = c_ulong()
        windll.user32.GetWindowThreadProcessId(self._handle, pointer(pid))

        # Get the process handle of this window's process ID.
        #  Access permission flags:
        #  0x0410 = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
        handle = windll.kernel32.OpenProcess(0x0410, 0, pid)

        # Retrieve and return the process's executable path.
        buf_len = 256
        buf = (c_wchar * buf_len)()
        windll.psapi.GetModuleFileNameExW(handle, 0, pointer(buf), buf_len)
        buf = buf[:]
        buf = buf[:buf.index("\0")]
        return str(buf)
    executable = property(fget=_get_window_module)


    #-----------------------------------------------------------------------
    # Methods related to window geometry.

    def get_position(self):
        l, t, r, b = self._get_rect()
        w = r - l; h = b - t
        return Rectangle(l, t, w, h)

    def set_position(self, rectangle):
        assert isinstance(rectangle, Rectangle)
        l, t, w, h = rectangle.ltwh
        win32gui.MoveWindow(self._handle, l, t, w, h, 1)

    def get_containing_monitor(self):
        center = self.get_position().center
        for monitor in monitors:
            if monitor.rectangle.contains(center):
                return monitor
        # Fall through, return first monitor.
        return monitors[0]

    def get_normalized_position(self):
        monitor = self.get_containing_monitor()
        rectangle = self.get_position()
        rectangle.renormalize(monitor.rectangle, unit)
        return rectangle

    def set_normalized_position(self, rectangle, monitor=None):
        if not monitor: monitor = self.get_containing_monitor()
        rectangle.renormalize(unit, monitor.rectangle)
        self.set_position(rectangle)

    #-----------------------------------------------------------------------
    # Methods for miscellaneous window control.

    def set_foreground(self):
        if self.is_minimized:
            self.restore()
        self._set_foreground()
