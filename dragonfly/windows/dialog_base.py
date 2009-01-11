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
This file implements a Win32 dialog base class.
"""


#---------------------------------------------------------------------------

import sys
import ctypes
import struct
import winxpgui as win32gui
import win32api
import win32con
import os
from ctypes.wintypes import POINT


#---------------------------------------------------------------------------

class MINMAXINFO(ctypes.Structure):
    _fields_ = [
                ("ptReserved",      POINT),
                ("ptMaxSize",       POINT),
                ("ptMaxPosition",   POINT),
                ("ptMinTrackSize",  POINT),
                ("ptMaxTrackSize",  POINT),
               ]


#---------------------------------------------------------------------------

class DialogBase(object):

    _dialog_registered_windowclass = False
    _dialog_atom = None

    @classmethod
    def _dialog_register_windowclass(cls, instance, name):
        if not cls._dialog_registered_windowclass:
            wc = win32gui.WNDCLASS()
            wc.SetDialogProc()
            wc.hInstance = instance
            wc.lpszClassName = name
            wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
            wc.hCursor = win32gui.LoadCursor( 0, win32con.IDC_ARROW )
            wc.hbrBackground = win32con.COLOR_WINDOW + 1
            wc.lpfnWndProc = {}

            # C code: wc.cbWndExtra = DLGWINDOWEXTRA + sizeof(HBRUSH) + (sizeof(COLORREF));
            wc.cbWndExtra = win32con.DLGWINDOWEXTRA + struct.calcsize("Pi")

            cls._dialog_atom = win32gui.RegisterClass(wc)
            cls._dialog_registered_windowclass = True

        return cls._dialog_atom


    #-----------------------------------------------------------------------

    def __init__(self, classname, title, initial_size, initial_position,
                 min_size, max_size, style, font, modal=False):

        self._dialog_classname = classname
        self._dialog_initial_size = initial_size
        self._dialog_initial_position = initial_position
        self._dialog_min_size = min_size
        self._dialog_max_size = max_size
        self._dialog_title = title
        self._dialog_font = font
        self._dialog_style = style
        self._dialog_modal = modal

        win32gui.InitCommonControls()
        self._hinst = win32gui.dllhandle
        self._dialog_controls = []

        self._dialog_register_windowclass(self._hinst, classname)

    def _dialog_create(self, template, message_map):
        if self._dialog_modal:  function = win32gui.DialogBoxIndirect
        else:                   function = win32gui.CreateDialogIndirect
        function(self._hinst, template, 0, message_map)

    def _dialog_build_template(self):
        # Initialize dialog template with header.
        dialog_template = [self._dialog_build_header()]

        # Create controls and append control entries to the dialog template.
        self._dialog_build_controls()
        w, h = self._dialog_initial_size
        for control in self._dialog_controls:
            dialog_template.append(control.template_entry(w, h))

        print "\n   ".join(str(value) for value in dialog_template)
        return dialog_template

    def _calculate_center(self, size):
        w, h = size
        desktop = win32gui.GetDesktopWindow()
        al, at, ar, ab = win32gui.GetWindowRect(desktop)
        cx = (ar-al)/2; cy = (ab-at)/2
        cx, cy = win32gui.ClientToScreen(desktop, (cx, cy))
        l = cx - w/2; t = cy - h/2
        return l, t


    #-----------------------------------------------------------------------
    # Property access to window info.

    hwnd = property(lambda self: self._hwnd)


    #-----------------------------------------------------------------------
    # Methods that control the creation and content of the window.

    def _dialog_build_header(self):
        """
            Method which creates window controls.

            This method should be overridden by derived window classes
            to create the desired contents.

            http://docs.activestate.com/activepython/2.5/pywin32/Dialog_Header_Tuple.html

        """

        return [
                self._dialog_title,
                tuple(self._dialog_initial_position)
                 + tuple(self._dialog_initial_size),
                self._dialog_style,
                None,
                self._dialog_font,
                None,
                self._dialog_classname,
               ]

    def _dialog_build_controls(self):
        """
            Method which creates window controls.

            This method should be overridden by derived window classes
            to create the desired contents.

        """

        pass

    def add_control(self, control):
        """
            Register the given *control* as a child of this window.

            This method is generally called by the constructor of
            Control instances.  It is therefore usually not necessary for
            users to call it directly.

        """

        self._dialog_controls.append(control)

    def _dialog_build_message_map(self):
        # Collect all controls which expect callbacks.
        map = {}
        for control in self._dialog_controls:
            for message, callback in control.message_callbacks.items():
                map.setdefault(message, {})[control.id] = callback

        # Create dispatchers for each type of message.
        for message, control_callbacks in map.items():
            def dispatcher(hwnd, msg, wparam, lparam):
                id = win32api.LOWORD(wparam)
                if id in control_callbacks:
                    control_callbacks[id](hwnd, msg, wparam, lparam)
            map[message] = dispatcher

        # Add the top-level callbacks handled by the window itself.
        map.update({
                    win32con.WM_SIZE:           self.on_size,
                    win32con.WM_INITDIALOG:     self.on_init_dialog,
                    win32con.WM_GETMINMAXINFO:  self.on_getminmaxinfo,
                    win32con.WM_CLOSE:          self.on_close,
                    win32con.WM_DESTROY:        self.on_destroy,
                  })
        return map


    #-----------------------------------------------------------------------
    # Message handler methods.

    def _get_edge_sizes(self):
        wl, wt, wr, wb = win32gui.GetWindowRect(self._hwnd)
        cl, ct, cr, cb = win32gui.GetClientRect(self._hwnd)
        il, it = win32gui.ClientToScreen(self._hwnd, (cl, ct))
        ir, ib = win32gui.ClientToScreen(self._hwnd, (cr, cb))
        el = il - wl
        et = it - wt
        er = wr - ir
        eb = wb - ib
        return el, et, er, eb

    def tracer (function):
        if hasattr(function, 'im_func'): name = function.im_func.func_name
        else: name = function.func_name
        def decorated (*a, **k):
            print "call", name, "arguments:", a,k
            return function(*a, **k)
        return decorated

    @tracer
    def on_init_dialog(self, hwnd, msg, wparam, lparam):
        self._hwnd = hwnd

        l, t = self._dialog_initial_position
        el, et, er, eb = self._get_edge_sizes()
        w = self._dialog_initial_size[0] + el + er
        h = self._dialog_initial_size[1] + et + eb
        win32gui.MoveWindow(self._hwnd, l, t, w, h, 0)

        l, t, r, b = win32gui.GetWindowRect(self._hwnd)
        w = r - l - el - er
        h = b - t - et - eb
        self._do_size(w, h, 1)

        self._post_init()

    def _post_init(self):
        """
            Method for performing any processing required after the
            main window has been initialized.

            This method should be overridden by derived window classes
            if they require anything to be done after the main window
            has been created and positioned.  This method is called
            after a WM_INITDIALOG message was received.

        """

        pass

    def on_size(self, hwnd, msg, wparam, lparam):
        width  = win32api.LOWORD(lparam)
        height = win32api.HIWORD(lparam)
        self._do_size(width, height)
        return 1

    def _do_size(self, width, height, repaint=1):
        for control in self._dialog_controls:
            l, t, w, h = control.calculate_size(width, height)
            win32gui.MoveWindow(control.handle, l, t, w, h, repaint)

    def on_getminmaxinfo(self, hwnd, msg, wparam, lparam):
        info = ctypes.cast(lparam, ctypes.POINTER(MINMAXINFO)).contents
        el, et, er, eb = self._get_edge_sizes()
        if self._dialog_max_size:
            width  = self._dialog_max_size[0] + el + er
            height = self._dialog_max_size[1] + et + eb
            point  = POINT(width, height)
            info.ptMaxSize       = point
            info.ptMaxTrackSize  = point
        if self._dialog_min_size:
            width  = self._dialog_min_size[0] + el + er
            height = self._dialog_min_size[1] + et + eb
            point  = POINT(width, height)
            info.ptMinTrackSize  = point

    def close(self):
        if self._dialog_modal:  win32gui.EndDialog(self._hwnd, 0)
        else:                   win32gui.DestroyWindow(self._hwnd)

    @tracer
    def on_close(self, hwnd, msg, wparam, lparam):
            self.close()

    @tracer
    def on_destroy(self, hwnd, msg, wparam, lparam):
        if not self._dialog_modal:
            win32gui.PostQuitMessage(0)


#---------------------------------------------------------------------------

class BasicDialog(DialogBase):

    def __init__(self, title, size, min_size=None, max_size=None, modal=False):
        classname  = "dragonfly.BasicDialog"
        position   = self._calculate_center(size)
        font       = (8, "MS Sans Serif")
        style      = ( win32con.WS_THICKFRAME
                     | win32con.WS_POPUP
                     | win32con.WS_VISIBLE
                     | win32con.WS_CAPTION
                     | win32con.WS_SYSMENU
                     | win32con.DS_SETFONT
                     | win32con.WS_MINIMIZEBOX)

        DialogBase.__init__(
                            self,
                            classname=classname,
                            title=title,
                            initial_size=size,
                            initial_position=position,
                            min_size=min_size,
                            max_size=max_size,
                            style=style,
                            font=font,
                            modal=modal,
                           )

        template = self._dialog_build_template()
        message_map = self._dialog_build_message_map()
        self._dialog_create(template, message_map)

