from dragonfly import *
from multiprocessing import Process, Queue

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

# def create_test_grammar():
#     grammar = Grammar('voxhub')                         # Create a grammar to contain the command rule.
#     grammar.add_rule(ExampleRule())                     # Add the command rule to the grammar.1
#     grammar.add_rule(ExampleRule2())
#     grammar.add_rule(ExampleRule3())
#     grammar.load()                                     # Load the grammar.
# def load_test_grammar():
#     grammar = Grammar("test", engine=get_engine("sphinx"))                       # Create a grammar to contain the command rule.
#     grammar.add_rule(ExampleRule())                     # Add the command rule to the grammar.1
#     grammar.load()                                      # Load the grammar.

# def load_test_grammar():
#     grammar = Grammar("example grammar")                       # Create a grammar to contain the command rule.
#     grammar.add_rule(ExampleRule())                     # Add the command rule to the grammar.1
#     grammar.add_rule(ExampleRule2())                     # Add the command rule to the grammar.1
#     grammar.load()

# Main file. Parse new commands from stdin until EOF.
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

from dragonfly.engines.backend_voxhub.mic import setup
if __name__ == '__main__':
    # load_test_grammar()
    engine = get_engine("voxhub")
    #
    load_test_grammar()
    engine.connect()
    engine.process_speech()
    import time
    time.sleep(10)
    # engine.disconnect()

    # q = Queue()
    # p = Process(target=setup, args=("silvius-server.voxhub.io",q,))
    # p.start()
    # while True:
    #     result = q.get()
    #     if result:
    #         print "IT WORKS"
    #         print result  # prints "[42, None, 'hello']"
    # p.join()
    #
    # print ("WOWOWOWOWOWOWOWOW")
    # observer = Observer(engine)
    # observer.register()
# if __name__ == '__main__':
#     import sys
#     # if len(sys.argv) > 1:
#     #     filename = sys.argv[1]
#     #     f = open(filename)
#     # else:
#     f = sys.stdin
#     # load_test_grammar()
#
#     # parser = SingleInputParser()
#     # find_keywords(parser)  # init lexer
#
#     while True:
#         line = f.readline()
#         if line == '': break
#         if line == '\n': continue
#
#         print ">", line
#         # try:
#         #     ast = parse(parser, scan(line))
#         #     printAST(ast)
#         #     execute(ast, f == sys.stdin)
#         # except GrammaticalError as e:
#         #     print "Error:", e
#
#     if f != sys.stdin:
#         f.close()
#
#     print 'ok'
