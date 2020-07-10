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
Window class for Windows
============================================================================

"""

# pylint: disable=E0401
# This file imports Win32-only symbols.

# pylint: disable=E0213,E1120,W0212
# Suppress warnings about _win32gui_func() lambdas and protected access.

from ctypes          import windll, pointer, c_wchar, c_ulong

import win32api
import win32con
import win32gui

from .base_window    import BaseWindow
from .rectangle      import Rectangle
from ..actions.action_key import Key


#===========================================================================

class Win32Window(BaseWindow):
    """
        The Window class is an interface to the Win32 window control
        and placement.

    """

    _results_box_class_names = ["#32770", "DgnResultsBoxWindow"]

    #-----------------------------------------------------------------------
    # Class methods to create new Window objects.

    @classmethod
    def get_foreground(cls):
        handle = win32gui.GetForegroundWindow()
        if handle in cls._windows_by_id:
            return cls._windows_by_id[handle]
        window = Win32Window(handle=handle)
        return window

    @classmethod
    def get_all_windows(cls):
        def function(handle, argument):
            argument.append(cls.get_window(handle))
        argument = []
        win32gui.EnumWindows(function, argument)
        return argument

    @classmethod
    def get_matching_windows(cls, executable=None, title=None):
        # Make window searches case-insensitive.
        if executable:
            executable = executable.lower()
        if title:
            title = title.lower()

        matching = []
        for window in cls.get_all_windows():
            if not window.is_visible:
                continue

            if executable:
                if window.executable.lower().find(executable) == -1:
                    continue
            if title:
                if window.title.lower().find(title) == -1:
                    continue

            if (window.executable.endswith("natspeak.exe")
                    and window.classname in cls._results_box_class_names
                    and window.get_position().dy < 50):
                # If a window matches the above, it is very probably
                #  the results-box of DNS.  We ignore this because
                #  its title is the words of the last recognition,
                #  which will often interfere with a search for
                #  a window with a spoken title.
                continue

            matching.append(window)

        return matching

#    @classmethod
#    def get_window_by_executable(cls, executable):
#        def function(handle, argument):
#            title = windll.user32.GetWindowText(handle)
#            print "title: %r" % title
#        windll.user32.EnumWindows(function, argument)


    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, handle):
        super(Win32Window, self).__init__(id=handle)

    def __repr__(self):
        args = ["handle=%d" % self.handle] + list(self._names)
        return "%s(%s)" % (self.__class__.__name__, ", ".join(args))

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

    def _win32gui_test(name):
        test = getattr(win32gui, name)
        fget = lambda self: test(self._handle) and True or False
        return property(fget=fget,
                        doc="Shortcut to win32gui.%s() function." % name)

    is_valid        = _win32gui_test("IsWindow")
    is_enabled      = _win32gui_test("IsWindowEnabled")
    is_visible      = _win32gui_test("IsWindowVisible")
    is_minimized    = _win32gui_test("IsIconic")

    @property
    def is_maximized(self):
        # IsZoomed() is not available from win32gui for some reason.
        # So we use the function directly.
        return bool(windll.user32.IsZoomed(self._handle))

    def _win32gui_show_window(state):
        return lambda self: win32gui.ShowWindow(self._handle, state)

    minimize        = _win32gui_show_window(win32con.SW_MINIMIZE)
    maximize        = _win32gui_show_window(win32con.SW_MAXIMIZE)
    restore         = _win32gui_show_window(win32con.SW_RESTORE)

    def _win32gui_post(message, w=0, l=0):
        return lambda self: win32gui.PostMessage(self._handle, message, w, l)

    close = _win32gui_post(win32con.WM_CLOSE)

    def _get_window_pid(self):
        # Get this window's process ID.
        pid = c_ulong()
        windll.user32.GetWindowThreadProcessId(self._handle, pointer(pid))
        return pid.value

    def _get_window_module(self):
        # Get this window's process ID.
        pid = self._get_window_pid()

        # Get the process handle of this window's process ID.
        #  Access permission flags:
        #  0x0410 = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
        handle = windll.kernel32.OpenProcess(0x0410, 0, pid)

        # Retrieve and return the process's executable path.
        try:
            # Try to use the QueryForProcessImageNameW function
            #  available since Windows Vista.
            buffer_len = c_ulong(256)
            buffer = (c_wchar * buffer_len.value)()
            windll.kernel32.QueryFullProcessImageNameW(handle, 0,
                                                       pointer(buffer),
                                                       pointer(buffer_len))
            buffer = buffer[:]
            buffer = buffer[:buffer.index("\0")]
        except Exception:
            # If the function above failed, fall back to the older
            #  GetModuleFileNameEx function, available since windows XP.
            #  Note that this fallback function seems to fail when
            #  this process is 32 bit Python and handle refers to a
            #  64-bit process.
            buffer_len = 256
            buffer = (c_wchar * buffer_len)()
            windll.psapi.GetModuleFileNameExW(handle, 0, pointer(buffer),
                                              buffer_len)
            buffer = buffer[:]
            buffer = buffer[:buffer.index("\0")]
        finally:
            windll.kernel32.CloseHandle(handle)

        return str(buffer)

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

    #-----------------------------------------------------------------------
    # Methods for miscellaneous window control.

    def set_foreground(self):
        # Bring this window into the foreground if it isn't already the
        # current foreground window.
        if self.handle != win32gui.GetForegroundWindow():
            if self.is_minimized:
                self.restore()

            # Press a key so Windows allows us to use SetForegroundWindow()
            # (received last input event). See Microsoft's documentation on
            # SetForegroundWindow() for why this works.
            # Only do this if neither the left or right control keys are
            # held down.
            if win32api.GetKeyState(win32con.VK_CONTROL) >= 0:
                Key("control:down,control:up").execute()

            # Set the foreground window.
            self._set_foreground()

    def set_focus(self):
        # Setting window focus without raising the window doesn't appear to
        # be possible in Windows, so fallback on set_foreground().
        self.set_foreground()
