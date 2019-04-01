"""
Dragonfly command module designed for use with the CMU Pocket Sphinx engine,
either with the module loader or as a script.

Shows use of dragonfly Functions, Lists, Repetition, Dictation, IntegerRefs,
Mimic, etc.
"""

from dragonfly import (Dictation, Function, Grammar, IntegerRef, List,
                       ListRef, MappingRule, RecognitionObserver, Mimic,
                       Repetition, RuleRef, get_engine, Text)


engine = get_engine("sphinx")


def disconnect():
    # You shouldn't really run this module in other engines because it uses
    # sphinx-specific engine methods.
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


def write_transcripts():
    engine.write_transcript_files(
        "training.fileids", "training.transcription"
    )


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

        # You still can use Mimic or engine.mimic() to match dictation.
        "say hello world": Mimic("hello", "WORLD"),

        # Update and recognise from a dragonfly list.
        "update list": Function(update_list),
        "<lst>": Function(lambda lst: print_(lst)),

        # Command to type numbers, e.g. 'type one two three'.
        "type <numbers>": Function(type_numbers),

        # Stop recognising from the microphone and exit.
        "disconnect engine|turn off": Function(disconnect),

        # Write transcript files used for training models.
        "(make|write) transcripts": Function(write_transcripts),
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

    observer = Observer()
    observer.register()

    # Start engine's main recognition loop
    try:
        engine.recognise_forever()
    except KeyboardInterrupt:
        pass
