#
# This file is a command-module for Dragonfly.
# (c) Copyright 2008 by Christo Butcher
# Licensed under the LGPL, see <http://www.gnu.org/licenses/>
#

"""
Command-module loader for natlink
=================================

This script can be used to look Dragonfly command-modules
for use with Dragon NaturallySpeaking.  It scans the
directory it's in and loads any ``_*.py`` it finds.

Some notes
----------

- Modules loaded by this script will **not** be re-loaded
  automatically.

- Messages printed from loaded modules will **not** show up
  in natlink's messages window because this script uses a
  separate process.

- Modules loaded normally via natlinkmain will still work
  and be recognized normally.

- This script will open a small dialog window via the
  ``natlink.waitForSpeech()`` function and will terminate
  when you click 'Close'.

- One use for this script is to control admin applications with
  Dragon. This can be done by simply running the script as the
  administrator with Dragon running and dragonfly's dependencies
  installed.

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
        __file__ = os.path.join(path, "dfly-loader-natlink.py")

    engine = get_engine("natlink")
    engine.connect()

    # Register a recognition observer
    observer = Observer()
    observer.register()

    directory = CommandModuleDirectory(path, excludes=[__file__])
    directory.load()

    # Recognize from Dragon in a loop (opens a dialogue window).
    engine.natlink.waitForSpeech()

    # Unload all grammars from the engine so that Dragon doesn't keep
    # recognizing them.
    for grammar in engine.grammars:
        grammar.unload()

    # Disconnect after the dialogue is closed.
    engine.disconnect()


if __name__ == "__main__":
    main()
