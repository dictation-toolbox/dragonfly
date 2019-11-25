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


from dragonfly import get_engine
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
        # tmp_dir='kaldi_model_zamia.tmp',  # default for temporary directory
        # vad_aggressiveness=3,  # default aggressiveness of VAD
        # vad_padding_start_ms=300,  # default ms of required silence before VAD
        # vad_padding_end_ms=100,  # default ms of required silence after VAD
        # vad_complex_padding_end_ms=500,  # default ms of required silence after VAD for complex utterances
        # input_device_index=None,  # set to an int to choose a non-default microphone
        # auto_add_to_user_lexicon=True,  # set to True to possibly use cloud for pronunciations
        # lazy_compilation=True,  # set to True to parallelize & speed up loading
        # cloud_dictation=None,  # set to 'gcloud' to use cloud dictation
        # retain_dir=None,  # set to a writable directory path to retain recognition metadata and/or audio data
        # retain_audio=None,  # set to True to retain speech data wave files in the retain_dir (if set)
    )

    # Call connect() now that the engine configuration is set.
    engine.connect()

    # Load grammars.
    directory = CommandModuleDirectory(path, excludes=[__file__])
    directory.load()

    # Define recognition callback functions.
    def on_begin():
        print("Speech start detected.")

    def on_recognition(words):
        print("Recognized: %s" % " ".join(words))

    def on_failure():
        print("Sorry, what was that?")

    # Start the engine's main recognition loop
    engine.prepare_for_recognition()
    try:
        engine.do_recognition(on_begin, on_recognition, on_failure)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
