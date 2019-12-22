from __future__ import print_function
import logging, os

import dragonfly

if False:
    logging.basicConfig(level=10)
    logging.getLogger('grammar.decode').setLevel(20)
    logging.getLogger('compound').setLevel(20)
    # logging.getLogger('kaldi').setLevel(30)
    logging.getLogger('engine').setLevel(10)
    logging.getLogger('kaldi').setLevel(10)
else:
    # logging.basicConfig(level=20)
    from dragonfly.log import setup_log
    setup_log()


class ExampleCustomRule(dragonfly.CompoundRule):

    spec = "I want to eat <food>"
    extras = [
        dragonfly.Choice(
            "food", {"(an | a juicy) apple": "good", "a [greasy] hamburger": "bad"}
        )
    ]

    def _process_recognition(self, node, extras):
        good_or_bad = extras["food"]
        print("That is a %s idea!" % good_or_bad)

class ExampleDictationRule(dragonfly.MappingRule):
    mapping = {
        "dictate <text>": dragonfly.Function(lambda text: print("I heard %r!" % str(text))),
    }
    extras = [ dragonfly.Dictation("text") ]


# Load engine before instantiating rules/grammars!
# Set any configuration options here as keyword arguments.
engine = dragonfly.get_engine("kaldi",
    model_dir='kaldi_model',
    # tmp_dir='kaldi_tmp',  # default for temporary directory
    # vad_aggressiveness=3,  # default aggressiveness of VAD
    # vad_padding_ms=300,  # default ms of required silence surrounding VAD
    # input_device_index=None,  # set to an int to choose a non-default microphone
    # cloud_dictation=None,  # set to 'gcloud' to use cloud dictation
)
# Call connect() now that the engine configuration is set.
engine.connect()

grammar = dragonfly.Grammar(name="mygrammar")
rule = ExampleCustomRule()
grammar.add_rule(rule)
grammar.add_rule(ExampleDictationRule())
grammar.load()

print('Try saying: "I want to eat an apple" or "I want to eat a greasy hamburger" or "dictate this is just a test"')
print("Listening...")
engine.do_recognition()
