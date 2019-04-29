#
# This file is a command-module for Dragonfly.
# (c) Copyright 2008 by Christo Butcher
# Licensed under the LGPL, see <http://www.gnu.org/licenses/>
#

"""
Command-module loader for WSR
=============================

This script can be used to look Dragonfly command-modules 
for use with Window Speech Recognition.  It scans the 
directory it's in and loads any ``_*.py`` it finds.

"""
import ctypes
import ctypes.wintypes
import time
import os.path
import logging
import pythoncom
import win32con

from dragonfly import RecognitionObserver, get_engine, Window
from dragonfly.loader import CommandModuleDirectory


#---------------------------------------------------------------------------
# Set up basic logging.

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("compound.parse").setLevel(logging.INFO)

# --------------------------------------------------------------------------
# Simple recognition observer class.

class Observer(RecognitionObserver):
    def __init__(self):
        super(Observer, self).__init__()

    def on_begin(self):
        print("Speech start detected.")

    def on_recognition(self, words):
        print(" ".join(words))

    def on_failure(self):
        print("Sorry, what was that?")


#---------------------------------------------------------------------------
# Main event driving loop.

def main():
    logging.basicConfig(level=logging.INFO)

    try:
        path = os.path.dirname(__file__)
    except NameError:
        # The "__file__" name is not always available, for example
        #  when this module is run from PythonWin.  In this case we
        #  simply use the current working directory.
        path = os.getcwd()
        __file__ = os.path.join(path, "dfly-loader-wsr.py")

    engine = get_engine("sapi5inproc")
    engine.connect()

    # Register a recognition observer
    observer = Observer()
    observer.register()

    directory = CommandModuleDirectory(path, excludes=[__file__])
    directory.load()

    WinEventProcType = ctypes.WINFUNCTYPE(None, ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD, ctypes.wintypes.HWND,
                                          ctypes.wintypes.LONG, ctypes.wintypes.LONG, ctypes.wintypes.DWORD,
                                          ctypes.wintypes.DWORD)

    def callback(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        window = Window.get_foreground()
        if hwnd == window.handle:
            for grammar in engine.grammars:
                grammar.process_begin(window.executable, window.title, window.handle)

    def set_hook(win_event_proc, event_type):
        return ctypes.windll.user32.SetWinEventHook(event_type, event_type, 0, win_event_proc, 0, 0, win32con.WINEVENT_OUTOFCONTEXT)


    win_event_proc = WinEventProcType(callback)
    ctypes.windll.user32.SetWinEventHook.restype = ctypes.wintypes.HANDLE

    [set_hook(win_event_proc, et) for et in
     {win32con.EVENT_SYSTEM_FOREGROUND, win32con.EVENT_OBJECT_NAMECHANGE, }]

    engine.speak('beginning loop!')
    while 1:
        pythoncom.PumpWaitingMessages()
        time.sleep(.1)

if __name__ == "__main__":
    main()
