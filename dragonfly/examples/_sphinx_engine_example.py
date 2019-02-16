"""
Dragonfly command module designed for use with the CMU Pocket Sphinx engine
backend.

Shows use of dragonfly Lists, Repetition, Dictation, IntegerRefs.

Maybe be used with other engines by changing the call to get_engine().
"""

from dragonfly import (Dictation, Function, Grammar, IntegerRef, List,
                       ListRef, MappingRule, RecognitionObserver,
                       Repetition, RuleRef, Text, get_engine)


# Set the engine to "sphinx". This file should be either run as a script or
# loaded with the Pocket Sphinx module loader.
engine = get_engine("sphinx")
if engine.name == "sphinx":
    engine.config.START_ASLEEP = False
    engine.config.TRAINING_DATA_DIR = ""


def disconnect():
    print("Disconnecting engine (only for sphinx)")
    if engine.name == "sphinx":
        engine.disconnect()


def print_(x):
    print(x)


# Set up a dragonfly list.
lst = List("lst")

def update_list():
    if lst:
        print("Removing item from list.")
        lst.pop()
    else:
        item = "list item"
        print("Added '%s' to the list." % item)
        lst.append(item)


# Define a rule for typing numbers.
numbers_rule = MappingRule(
    name="numbers", mapping={"<n>": Text("%(n)d")},
    exported=False, extras=[IntegerRef("n", 1, 20)]
)

# Define a function for executing the rule's actions.
def type_numbers(numbers):
    for n in numbers:
        n.execute()


class ExampleRule(MappingRule):
    mapping = {
        # Recognise 'hello' followed by arbitrary dictation.
        # This mapping cannot be matched using Pocket Sphinx because the
        # engine's support for dictation has been temporarily disabled.
        "hello <dictation>": Function(lambda dictation: print_(dictation)),

        # Update and recognise from a dragonfly list.
        "update list": Function(update_list),
        "<lst>": Function(lambda lst: print_(lst)),

        # Command to type numbers, e.g. 'type one two three'.
        "type <numbers>": Function(type_numbers),

        # Stop recognising from the microphone and exit.
        "disconnect engine|turn off": Function(disconnect),
    }

    extras = [
        Dictation("dictation"),
        ListRef("lst", lst),
        Repetition(RuleRef(rule=numbers_rule), min=1, max=16,
                   name="numbers"),
    ]


grammar = Grammar("test", engine=engine)
grammar.add_rule(ExampleRule())
grammar.load()


if __name__ == '__main__':
    # If this file is being run, not imported, set up a recognition observer
    # to print some info.

    class Observer(RecognitionObserver):
        def on_begin(self):
            print("Speech started.")

        def on_recognition(self, words):
            print(" ".join(words))

        def on_failure(self):
            print("Sorry, what was that?")

        def on_next_rule_part(self, words):
            print("Current words: %s" % " ".join(words))
            print("Awaiting next rule part...")

    observer = Observer()
    observer.register()
    engine.recognise_forever()
