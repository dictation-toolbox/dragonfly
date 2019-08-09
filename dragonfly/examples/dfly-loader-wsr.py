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

import os.path

from dragonfly import RecognitionObserver, get_engine
from dragonfly.loader import CommandModuleDirectory
from dragonfly.log import setup_log

#---------------------------------------------------------------------------
# Set up basic logging.

setup_log()
# logging.getLogger("compound.parse").setLevel(logging.INFO)

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

    # Recognize from WSR in a loop.
    engine.recognize_forever()


if __name__ == "__main__":
    main()
