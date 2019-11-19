"""
Dragonfly command module designed for use with the CMU Pocket Sphinx engine,
either with the module loader or as a script.

Shows use of dragonfly Functions, Lists, Repetition, Dictation, IntegerRefs,
Mimic, etc.
"""

from dragonfly import (Dictation, Function, Grammar, IntegerRef, List,
                       ListRef, MappingRule, RecognitionObserver, Mimic,
                       Repetition, get_engine, Text)


if __name__ == '__main__':
    # If this file is being run, not imported, then use the sphinx engine.
    sphinx_engine = get_engine("sphinx")


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
    engine = get_engine()
    if engine.name == "sphinx":
        engine.write_transcript_files(
            "training.fileids", "training.transcription"
        )


# Define a function for typing multiple numbers.
def type_numbers(numbers):
    Text("".join(map(str, numbers))).execute()


class ExampleRule(MappingRule):
    mapping = {
        # Recognise 'hello' followed by arbitrary dictation.
        # This mapping cannot be matched using Pocket Sphinx because the
        # engine's support for dictation has been temporarily disabled.
        "hello <dictation>": Function(print_, dict(dictation="x")),

        # You still can use Mimic or engine.mimic() to match dictation.
        "say hello world": Mimic("hello", "WORLD"),

        # Update and recognise from a dragonfly list.
        "update list": Function(update_list),
        "<lst>": Function(print_, dict(lst="x")),

        # Command to type numbers, e.g. 'type one two three'.
        "type <numbers>": Function(type_numbers),

        # Write transcript files used for training models.
        "(make|write) transcripts": Function(write_transcripts),
    }

    extras = [
        Dictation("dictation"),
        ListRef("lst", lst),
        Repetition(IntegerRef("n", 1, 20), min=1, max=16,
                   name="numbers"),
    ]


grammar = Grammar("Sphinx engine example")
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
        sphinx_engine.recognise_forever()
    except KeyboardInterrupt:
        pass
