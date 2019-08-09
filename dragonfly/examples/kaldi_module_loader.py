"""
Command-module loader for Kaldi.

This script is based on 'dfly-loader-wsr.py' written by Christo Butcher and
has been adapted to work with the Kaldi engine instead.

This script can be used to look for Dragonfly command-modules for use with
the Kaldi engine. It scans the directory it's in and loads any ``_*.py`` it
finds.
"""


# TODO Have a simple GUI for pausing, resuming, cancelling and stopping
# recognition, etc

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
    logging.getLogger('kaldi.compiler').setLevel(10)
else:
    setup_log()


# --------------------------------------------------------------------------
# Simple recognition observer class.

class Observer(RecognitionObserver):
    def on_begin(self):
        print("Speech started.")

    def on_recognition(self, words):
        print(" ".join(words))

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
        __file__ = os.path.join(path, "kaldi_module_loader.py")

    # Set any configuration options here as keyword arguments.
    engine = get_engine("kaldi",
        model_dir='kaldi_model_zamia',
        # tmp_dir='kaldi_tmp',  # default for temporary directory
        # vad_aggressiveness=3,  # default aggressiveness of VAD
        # vad_padding_ms=300,  # default ms of required silence surrounding VAD
        # input_device_index=None,  # set to an int to choose a non-default microphone
        # auto_add_to_user_lexicon=True,  # set to True to possibly use cloud for pronunciations
        # cloud_dictation=None,  # set to 'gcloud' to use cloud dictation
    )

    # Call connect() now that the engine configuration is set.
    engine.connect()

    # Register a recognition observer
    observer = Observer()
    observer.register()

    directory = CommandModuleDirectory(path, excludes=[__file__])
    directory.load()

    # Start the engine's main recognition loop
    try:
        # Loop forever
        engine.do_recognition()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
