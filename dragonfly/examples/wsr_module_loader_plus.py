"""
Command-module loader for WSR.

This script can be used to look for Dragonfly command-modules for use with
the WSR engine. It scans the directory it's in and loads any ``_*.py`` it
finds.
"""


# TODO Have a simple GUI for pausing, resuming, cancelling and stopping
# recognition, etc

from __future__ import print_function
import os.path
import logging
import winsound

from dragonfly import RecognitionObserver, get_engine
from dragonfly import Grammar, MappingRule, Function, Dictation, FuncContext
from dragonfly.loader import CommandModuleDirectory
from dragonfly.log import setup_log


# --------------------------------------------------------------------------
# Set up basic logging.

setup_log()


# --------------------------------------------------------------------------
# User notification / rudimentary UI. MODIFY AS DESIRED

# For message in ('sleep', 'wake')
def notify(message):
    if message == 'sleep':
        print("Sleeping...")
        # get_engine().speak("Sleeping")
        play_sound('sleep')
    elif message == 'wake':
        print("Awake...")
        # get_engine().speak("Awake")
        play_sound('on')

sound_mappings = {
    "on":               r"C:\Windows\media\Speech On.wav",
    "sleep":            r"C:\Windows\media\Speech Sleep.wav",
    "off":              r"C:\Windows\media\Speech Off.wav",
    "what":             r"C:\Windows\media\Speech Misrecognition.wav",
    "dis":              r"C:\Windows\media\Speech Disambiguation.wav",
    "disambiguation":   r"C:\Windows\media\Speech Disambiguation.wav",
    "ack":              r"C:\Windows\media\Speech Disambiguation.wav",
}

def play_sound(sound, async=True):
    if sound in sound_mappings: sound = sound_mappings[sound]
    winsound.PlaySound(sound, winsound.SND_FILENAME | (winsound.SND_ASYNC if async else 0))


# --------------------------------------------------------------------------
# Sleep/wake grammar.

sleeping = False

def load_sleep_wake_grammar(initial_awake):
    sleep_grammar = Grammar("sleep")

    def sleep(force=False):
        global sleeping
        if not sleeping or force:
            sleeping = True
            sleep_grammar.set_exclusiveness(True)
            get_engine().process_grammars_context()
        notify('sleep')

    def wake(force=False):
        global sleeping
        if sleeping or force:
            sleeping = False
            sleep_grammar.set_exclusiveness(False)
            get_engine().process_grammars_context()
        notify('wake')

    class SleepRule(MappingRule):
        mapping = {
            "start listening":  Function(wake),
            "stop listening":   Function(sleep),
            "halt listening":   Function(sleep),
        }
    sleep_grammar.add_rule(SleepRule())

    sleep_noise_rule = MappingRule(
        name = "sleep_noise_rule",
        mapping = { "<text>": Function(lambda text: False and print(text)) },
        extras = [ Dictation("text") ],
        context = FuncContext(lambda: sleeping),
    )
    sleep_grammar.add_rule(sleep_noise_rule)

    sleep_grammar.load()

    if initial_awake:
        wake(force=True)
    else:
        sleep(force=True)


# --------------------------------------------------------------------------
# Simple recognition observer class.

class Observer(RecognitionObserver):
    def on_begin(self):
        print("Speech started.")

    def on_recognition(self, words):
        print("Recognized:", " ".join(words))

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
        __file__ = os.path.join(path, "wsr_module_loader_plus.py")

    # Set any configuration options here as keyword arguments.
    engine = get_engine("sapi5inproc")

    # Call connect() now that the engine configuration is set.
    engine.connect()

    # Register a recognition observer
    observer = Observer()
    observer.register()

    load_sleep_wake_grammar(True)

    directory = CommandModuleDirectory(path, excludes=[__file__])
    directory.load()

    # Start the engine's main recognition loop
    try:
        # Recognize from WSR in a loop.
        print("Listening...")
        engine.recognize_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
