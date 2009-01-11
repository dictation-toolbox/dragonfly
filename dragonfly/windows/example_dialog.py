

import sys
import ctypes
import struct
import winxpgui as win32gui
import win32api
import win32con
import threading
import Queue
import os
from ctypes.wintypes import POINT

import pkg_resources
pkg_resources.require("dragonfly >= 0.6.4rc3.dev_r57")

from dragonfly.all import Clipboard

from dragonfly.windows.dialog_base import BasicDialog
from dragonfly.windows.control_base import ControlBase as Control
from dragonfly.windows.control_output import OutputText
from dragonfly.windows.control_button import Button



class DragonflyUpdaterWindow(BasicDialog):

    def __init__(self, modal=False):
        BasicDialog.__init__(
                             self,
                             "Dragonfly updater",
                             (300, 250),
                             min_size=(500, 250),
                             modal=modal,
                            )

    def _dialog_build_controls(self):
#        self.close_control =  Control(
#                                      self,
#                                      128,
#                                      "Close",
#                                      lambda w, h: (w-405, h-35, 125, 29),
#                                      style=( win32con.WS_CHILD
#                                            | win32con.WS_VISIBLE
#                                            | win32con.WS_TABSTOP
#                                            | win32con.BS_DEFPUSHBUTTON),
#                                      on_command=self.on_button_close,
#                                     )
        self.close_control =  Button(
                                      self,
                                      "Close",
                                      lambda w, h: (w-405, h-35, 125, 29),
                                      on_command=self.on_button_close,
                                     )
        self.update_control = Control(
                                      self,
                                      128,
                                      "Update dragonfly",
                                      lambda w, h: (w-270, h-35, 125, 29),
                                      style=( win32con.WS_CHILD
                                            | win32con.WS_VISIBLE
                                            | win32con.WS_TABSTOP
                                            | win32con.BS_PUSHBUTTON),
                                      on_command=self.on_button_update,
                                     )
        self.copy_control =   Control(
                                      self,
                                      128,
                                      "Copy to clipboard",
                                      lambda w, h: (w-135, h-35, 125, 29),
                                      style=( win32con.WS_CHILD
                                            | win32con.WS_VISIBLE
                                            | win32con.WS_TABSTOP
                                            | win32con.BS_PUSHBUTTON),
                                      on_command=self.on_button_copy,
                                     )
        self.label_control  = Control(
                                      self,
                                      130,
                                      "Output:",
                                      lambda w, h: (9, 5, w-10, 19),
                                      style=( win32con.WS_CHILD
                                            | win32con.WS_VISIBLE
                                            | win32con.ES_LEFT),
                                     )
        self.output_control = OutputText(
                                      self,
                                      lambda w, h: (5, 28, w-10, h-68),
                                     )

    def _post_init(self):
        # Redirect standard output and error to output control.
        sys.stdout = self.output_control
        sys.stderr = self.output_control

        # Determine and display current version of Dragonfly library.
        dragonfly_dist = pkg_resources.get_distribution("dragonfly")
        print "Current Dragonfly version:", dragonfly_dist.version

    def on_button_close(self, hwnd, msg, wparam, lparam):
        self.close()

    def on_button_update(self, hwnd, msg, wparam, lparam):
        thread = UpdateThread(self)
        self.update_start()
        thread.start()

    def on_button_copy(self, hwnd, msg, wparam, lparam):
        content = self.output_control.text
        Clipboard.set_text(content)

    def update_start(self):
        h = self.update_control.handle
        style = win32gui.GetWindowLong(h, win32con.GWL_STYLE)
        style |= win32con.WS_DISABLED
        win32gui.SetWindowLong(h, win32con.GWL_STYLE, style)
        win32gui.SendMessage(h, win32con.WM_ENABLE, 0, 0)
        win32gui.SetFocus(self.copy_control.handle)

    def update_done(self):
        h = self.update_control.handle
        style = win32gui.GetWindowLong(h, win32con.GWL_STYLE)
        style &= (~win32con.WS_DISABLED)
        win32gui.SetWindowLong(h, win32con.GWL_STYLE, style)
        win32gui.SendMessage(h, win32con.WM_ENABLE, 1, 0)


#---------------------------------------------------------------------------

class UpdateThread(threading.Thread):

    def __init__(self, window):
        self._window = window
        threading.Thread.__init__(self)

    def run(self):
        print
        print "Updating Dragonfly library"
        print

        try:
            entry_point = pkg_resources.load_entry_point(
                                                         'setuptools',
                                                         'console_scripts',
                                                         'easy_install'
                                                        )
            entry_point(["--dry-run", "--verbose", "--upgrade", "dragonfly"])
        except Exception, e:
            print
            print "Updating Dragonfly library failed:", e
            print
        else:
            print
            print "Updating Dragonfly library complete"
            print
        self._window.update_done()


#---------------------------------------------------------------------------
    
if __name__ == "__main__":
    w = DragonflyUpdaterWindow()
    win32gui.PumpMessages()
