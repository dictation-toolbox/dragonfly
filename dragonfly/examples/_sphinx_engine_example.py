"""
CMU Pocket Sphinx engine example using a few dragonfly classes
"""

import time
from dragonfly import *


def pause(n):
    print("Pausing for %d seconds" % n)
    g.engine.pause_recognition()
    time.sleep(n)
    g.engine.resume_recognition()
    print("Resuming")


def disconnect():
    print("Disconnecting engine")
    g.engine.disconnect()


class TestRule(MappingRule):
    mapping = {
        "disconnect engine": Function(disconnect),
        "hello <dictation>": ActionBase(),
        "more <dictation> stuff and <dictation>": ActionBase(),
        "pause for <n> seconds": Function(pause),
    }

    extras = [
        Dictation("dictation"),
        IntegerRef("n", 1, 20),
    ]

g = Grammar("test", engine=get_engine("sphinx"))
g.add_rule(TestRule())
g.load()


if __name__ == '__main__':
    # If this file is being run, not imported, set up the engine and an observer
    # to print some info.

    class Observer(RecognitionObserver):
        def on_begin(self):
            print("Speech started.")

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

    observer = Observer()
    observer.register()
    g.engine.recognise_forever()
