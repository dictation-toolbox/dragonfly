"""
Command-module loader for Voxhub/Silvius.

This script can be used to look for Dragonfly command-modules for use with
the Voxhub engine. It scans the directory it's in and loads any ``_*.py``
it finds.
"""

import os.path
import logging


from dragonfly import RecognitionObserver, get_engine
from dragonfly.loader import CommandModuleDirectory
from dragonfly.log import setup_log

# --------------------------------------------------------------------------
# Set up basic logging.

if False:
    # Debugging logging for reporting trouble
    logging.basicConfig(level=10)
    logging.getLogger('grammar.decode').setLevel(20)
    logging.getLogger('grammar.begin').setLevel(20)
    logging.getLogger('compound').setLevel(20)
else:
    setup_log()


# --------------------------------------------------------------------------
# Simple recognition observer class.

class Observer(RecognitionObserver):
    def on_begin(self):
        print("Speech started.")

    def on_recognition(self, words):
        print("Recognized: '%s'" % " ".join(words))

    def on_failure(self):
        print("Sorry, what was that?")


# --------------------------------------------------------------------------
# Main event driving loop.

def main():
    logging.basicConfig(level=logging.INFO)

    try:
        path = os.path.dirname(__file__)
    except NameError:
        # The "__file__" name is not always available, for example
        # when this module is run from PythonWin.  In this case we
        # simply use the current working directory.
        path = os.getcwd()
        __file__ = os.path.join(path, "voxhub_module_loader.py")

    # Initialize the engine and connect.
    engine = get_engine("voxhub")
    # engine.list_available_microphones()
    # engine.dump_grammar()
    engine.connect(process_speech=False)  # load grammars before listening.

    # Register a recognition observer
    observer = Observer()
    observer.register()

    directory = CommandModuleDirectory(path, excludes=[__file__])
    directory.load()

    # Start the engine's main recognition loop
    try:
        # Loop forever
        engine.process_speech()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
