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
        "disconnect": Function(disconnect),
        "hello <dictation>": ActionBase(),
        "more <dictation> stuff and <dictation>": ActionBase(),
        "pause for <n> seconds": Function(pause),
    }

    extras = [
        Dictation("dictation"),
        Choice("n", {
            "one": 1,
            "five": 5,
            "ten": 10
        })
    ]

g = Grammar("test")
g.add_rule(TestRule())
g.load()
