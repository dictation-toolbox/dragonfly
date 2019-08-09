"""
Multiple dictation constructs
===============================================================================

This file is a showcase investigating the use and functionality of multiple
dictation elements within Dragonfly speech recognition grammars.

The first part of this file (i.e. the module's doc string) contains a 
description of the functionality being investigated along with test code 
and actual output in doctest format. This allows the reader to see what 
really would happen, without needing to load the file into a speech 
recognition engine and put effort into speaking all the showcased 
commands.

The test code below makes use of Dragonfly's built-in element testing tool.
When run, it will connect to the speech recognition engine, load the element
being tested, mimic recognitions, and process the recognized value.


Multiple consecutive dictation elements
-------------------------------------------------------------------------------

>>> tester = ElementTester(RuleRef(ConsecutiveDictationRule()))
>>> print(tester.recognize("consecutive Alice Bob Charlie"))
Recognition: "consecutive Alice Bob Charlie"
Word and rule pairs: ("1000000" is "dgndictation")
 - consecutive (1)
 - Alice (1000000)
 - Bob (1000000)
 - Charlie (1000000)
Extras:
 - dictation1: Alice
 - dictation2: Bob
 - dictation3: Charlie

>>> print(tester.recognize("consecutive Alice Bob"))
RecognitionFailure


Mixed literal and dictation elements
-------------------------------------------------------------------------------

Here we will investigate mixed, i.e. interspersed, fixed literal command
words and dynamic dictation elements. We will use the "MixedDictationRule"
class which has a spec of
"mixed [<dictation1>] <dictation2> command <dictation3>".

Note that "<dictation1>" was made optional instead of "<dictation2>" 
because otherwise the first dictation elements would always gobble up 
all dictated words. There would (by definition) be no way to distinguish 
which words correspond with which dictation elements. Such consecutive 
dictation elements should for that reason be avoided in real command 
grammars. The way the spec is defined now, adds some interesting 
dynamics, because of the order in which they dictation elements parse 
the recognized words. However, do note that that order is well defined 
but arbitrarily chosen. 

>>> tester = ElementTester(RuleRef(MixedDictationRule()))
>>> print(tester.recognize("mixed Alice Bob command Charlie"))
Recognition: "mixed Alice Bob command Charlie"
Word and rule pairs: ("1000000" is "dgndictation")
 - mixed (1)
 - Alice (1000000)
 - Bob (1000000)
 - command (1)
 - Charlie (1000000)
Extras:
 - dictation1: Alice
 - dictation2: Bob
 - dictation3: Charlie

>>> print(tester.recognize("mixed Alice command Charlie"))
Recognition: "mixed Alice command Charlie"
Word and rule pairs: ("1000000" is "dgndictation")
 - mixed (1)
 - Alice (1000000)
 - command (1)
 - Charlie (1000000)
Extras:
 - dictation2: Alice
 - dictation3: Charlie

>>> print(tester.recognize("mixed Alice Bob command"))
RecognitionFailure

>>> print(tester.recognize("mixed command Charlie"))
RecognitionFailure


Repetition of dictation elements
-------------------------------------------------------------------------------

Now let's take a look at repetition of dictation elements. For this
we will use the "RepeatedDictationRule" class, which defines its spec
as a repetition of "command <dictation>". I.e. "command Alice" will
match, and "command Alice command Bob" will also match.

Note that this rule is inherently ambiguous, given the lack of a
clear definition of grouping or precedence rules for fixed literal
words in commands, and dynamic dictation elements. As an example,
"command Alice command Bob" could either match 2 repetitions with
"Alice" and "Bob" as dictation values, or a single repetition with
"Alice command Bob" as its only dictation value. The tests below
the show which of these actually occurs.

>>> tester = ElementTester(RuleRef(RepeatedDictationRule()))
>>> print(tester.recognize("command Alice"))
Recognition: "command Alice"
Word and rule pairs: ("1000000" is "dgndictation")
 - command (1)
 - Alice (1000000)
Extras:
 - repetition: [[u'command', NatlinkDictationContainer(Alice)]]

>>> print(tester.recognize("command Alice command Bob"))
Recognition: "command Alice command Bob"
Word and rule pairs: ("1000000" is "dgndictation")
 - command (1)
 - Alice (1000000)
 - command (1000000)
 - Bob (1000000)
Extras:
 - repetition: [[u'command', NatlinkDictationContainer(Alice, command, Bob)]]

"""


#---------------------------------------------------------------------------

import doctest
from dragonfly                          import *
from dragonfly.test.infrastructure      import RecognitionFailure
from dragonfly.test.element_testcase    import ElementTestCase
from dragonfly.test.element_tester      import ElementTester


#---------------------------------------------------------------------------

class RecognitionAnalysisRule(CompoundRule):
    """
        Base class that implements reporting in human-readable format
        details about the recognized phrase. It is used by the actual
        testing rules below, and allows the doctests above to be easily
        readable and informative.

    """

    def _process_recognition(self, node, extras):
        Paste(text).execute()

    def value(self, node):
        return self.get_recognition_info(node)

    def get_recognition_info(self, node):
        output = []
        output.append('Recognition: "{0}"'.format(" ".join(node.words())))
        output.append('Word and rule pairs: ("1000000" is "dgndictation")')
        for word, rule in node.full_results():
            output.append(" - {0} ({1})".format(word, rule))
        output.append("Extras:")
        for key in sorted(extra.name for extra in self.extras):
            extra_node = node.get_child_by_name(key)
            if extra_node:
                output.append(" - {0}: {1}".format(key, extra_node.value()))
        return "\n".join(output)


#---------------------------------------------------------------------------

class ConsecutiveDictationRule(RecognitionAnalysisRule):

    spec   = "consecutive <dictation1> <dictation2> <dictation3>"
    extras = [Dictation("dictation1"),
              Dictation("dictation2"),
              Dictation("dictation3")]


#---------------------------------------------------------------------------

class MixedDictationRule(RecognitionAnalysisRule):

    spec   = "mixed [<dictation1>] <dictation2> command <dictation3>"
    extras = [Dictation("dictation1"),
              Dictation("dictation2"),
              Dictation("dictation3")]


#---------------------------------------------------------------------------

class RepeatedDictationRule(RecognitionAnalysisRule):

    spec   = "<repetition>"
    extras = [Repetition(name="repetition",
                         child=Sequence([Literal("command"),
                                         Dictation()]))]


#---------------------------------------------------------------------------

def main():
    engine = get_engine()
    engine.connect()
    try:
        doctest.testmod(verbose=True)
    finally:
        engine.disconnect()

if __name__ == "__main__":
    main()
