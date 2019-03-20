from dragonfly import *

# Voice command rule combining spoken form and recognition processing.
class ExampleRule(CompoundRule):
    spec = "do something computer"                  # Spoken form of command.
    def _process_recognition(self, node, extras):   # Callback when command is spoken.
        print("Voice command spoken.")

class ExampleRule2(CompoundRule):
    spec = "I want to eat <food>"
    extras = [Choice("food", {
        "(an | a juicy) apple": "good",
        "a [greasy] hamburger": "bad",
    }
                     )
              ]

    def _process_recognition(self, node, extras):
        good_or_bad = extras["food"]
        print "That is a %s idea!" % good_or_bad

class ExampleRule3(CompoundRule):
    spec = "do"  # Spoken form of command.

    def _process_recognition(self, node, extras):  # Callback when command is spoken.
        print("Done!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

class ExampleRule4(CompoundRule):
    spec = "now"  # Spoken form of command.

    def _process_recognition(self, node, extras):  # Callback when command is spoken.
        print("Nowwwwwwwwwww!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
# Create a grammar which contains and loads the command rule.

def load_test_grammar():
    grammar = Grammar('voxhub')                         # Create a grammar to contain the command rule.
    grammar.add_rule(ExampleRule())                     # Add the command rule to the grammar.1
    grammar.add_rule(ExampleRule2())
    grammar.add_rule(ExampleRule3())
    grammar.add_rule(ExampleRule4())
    grammar.load()                                     # Load the grammar.

if __name__ == '__main__':
    # load_test_grammar()
    engine = get_engine("voxhub")
    #
    load_test_grammar()
    engine.connect()
    engine.process_speech()