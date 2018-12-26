"""
Command-module loader for CMU Pocket Sphinx.

This script is based on 'dfly-loader-wsr.py' written by Christo Butcher and
has been adapted to work with the Sphinx engine instead.

This script can be used to look for Dragonfly command-modules for use with
the CMU Pocket Sphinx engine. It scans the directory it's in and loads any
``_*.py`` it finds.
"""


import os.path
import logging


from dragonfly import RecognitionObserver, EngineError
from dragonfly.engines import get_engine
from dragonfly.engines.backend_sphinx.engine import SphinxEngine
from dragonfly.loader import CommandModuleDirectory

# --------------------------------------------------------------------------
# Set up basic logging.

logging.basicConfig(level=logging.INFO)
logging.getLogger("compound.parse").setLevel(logging.INFO)


# --------------------------------------------------------------------------
# Simple recognition observer class.

class Observer(RecognitionObserver):
    def __init__(self, engine):
        self.engine = engine
        super(Observer, self).__init__()

    def on_begin(self):
        if self.engine.recognising_dictation:
            print("Speech started. Processing as dictation.")
        else:
            print("Speech started using grammar search.")

    @staticmethod
    def _get_words(words_list):
        # Get just the words from the tuple list
        return " ".join([word for word, _ in words_list])

    def on_recognition(self, words_list):
        print(self._get_words(words_list))

    def on_failure(self):
        print("Sorry, what was that?")

    def on_next_rule_part(self, words_list):
        print("Current words: %s" % self._get_words(words_list))
        print("Awaiting next rule part...")


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
        __file__ = os.path.join(path, "sphinx_module_loader.py")

    engine = get_engine("sphinx")
    assert isinstance(engine, SphinxEngine)

    # Try to import the local engine configuration object first. If there isn't one,
    # use the default engine configuration.
    log = logging.getLogger("config")
    try:
        import config
        engine.config = config
        log.info("Using local engine configuration module 'config.py'")
    except ImportError:
        pass
    except EngineError as e:
        # Log EngineErrors caught when setting the configuration.
        log.warning(e)
        log.warning("Falling back to using the default engine configuration "
                    "instead of 'config.py'")

    # Call connect() now that the engine configuration is set.
    engine.connect()

    # Register a recognition observer
    observer = Observer(engine)
    observer.register()

    directory = CommandModuleDirectory(path, excludes=[__file__])
    directory.load()

    # TODO Have a simple GUI for pausing, resuming, cancelling and stopping recognition, etc
    # TODO Change script to import all modules before loading the grammars into Pocket Sphinx

    # Start the engine's main recognition loop
    try:
        engine.recognise_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
