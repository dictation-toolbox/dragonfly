"""
NatLink importable rules dgndictation, dgnletters and dgnwords
===============================================================================

This file is a showcase of the three importable rules provided by 
NatLink: "dgndictation", "dgnletters" and "dgnwords". 

The test code below makes use of Dragonfly's built-in element testing 
tool. When run, it will connect to the speech recognition engine, load 
the element being tested, mimic recognitions, and process the recognized 
value. 

"""


#---------------------------------------------------------------------------

import doctest
from dragonfly                          import *
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
        output.append("Word and rule pairs:")
        for word, rule in node.full_results():
            output.append(" - {0} ({1})".format(word, rule))
        output.append("Extras:")
        for key in sorted(extra.name for extra in self.extras):
            extra_node = node.get_child_by_name(key)
            if extra_node:
                output.append(" - {0}: {1}".format(key, extra_node.value()))
        return "\n".join(output)


#---------------------------------------------------------------------------

class DgnImported(RuleRef):
    """
        Base class that implements an imported rule and takes care of
        decoding recognitions accordingly.

    """

    def __init__(self, name=None, imported_name=None, default=None):
        if not imported_name:
            imported_name = name
        self.imported_name = imported_name
        self.imported_rule = Rule(self.imported_name, imported=True)
        RuleRef.__init__(self, self.imported_rule, name, default=default)

    def decode(self, state):
        state.decode_attempt(self)

        # Check that at least one word has been dictated, otherwise fail.
        rule1 = state.rule()  # actual rule name
        rule2 = self.imported_name  # expected rule name
        guessing = state.dictated_word_guesses
        if not guessing and rule1 != rule2 or rule1 is None:
            state.decode_failure(self)
            return

        # Check if guessing which words are dictated words is necessary.
        if rule1 == rule2:
            guessing = False

        # Determine how many words have been dictated.
        count = 1
        while state.rule(count) == rule1:
            count += 1

        # Yield possible states where the number of dictated words
        # gobbled is decreased by 1 between yields.
        # If guessing, be conservative instead and gobble as few of
        # the next words as possible, since they may not be dictated
        # words.
        if not guessing:
            deltas = range(count, 0, -1)
        else:
            deltas = range(1, count + 1, 1)
        for i in deltas:
            state.next(i)
            state.decode_success(self)
            yield state
            state.decode_retry(self)
            state.decode_rollback(self)

        # None of the possible states were accepted, failure.
        state.decode_failure(self)
        return

    def value(self, node):
        return node.words()


#---------------------------------------------------------------------------

class DgnDictationRule(RecognitionAnalysisRule):
    """
        >>> tester = ElementTester(RuleRef(DgnDictationRule()))
        >>> print(tester.recognize("dictation hello world"))
        Recognition: "dictation hello world"
        Word and rule pairs:
         - dictation (1)
         - hello (1000000)
         - world (1000000)
        Extras:
         - dgndictation: [u'hello', u'world']

        >>> print(tester.recognize("dictation"))
        RecognitionFailure

    """

    spec   = "dictation <dgndictation>"
    extras = [DgnImported("dgndictation")]


#---------------------------------------------------------------------------

class DgnLettersRule(RecognitionAnalysisRule):
    """
        >>> tester = ElementTester(RuleRef(DgnLettersRule()))
        >>> print(tester.recognize("letters a b c"))
        Recognition: "letters a\\\\l b\\\\l c\\letter-c\\l"
        Word and rule pairs:
         - letters (1)
         - a\\\\l (1000001)
         - b\\\\l (1000001)
         - c\\letter-c\\l (1000001)
        Extras:
         - dgnletters: [u'a\\\\\\\\l', u'b\\\\\\\\l', u'c\\\\letter-c\\\\l']

        >>> print(tester.recognize("letters hello world"))
        RecognitionFailure

        >>> print(tester.recognize("letters"))
        RecognitionFailure

    """

    spec   = "letters <dgnletters>"
    extras = [DgnImported("dgnletters")]


#---------------------------------------------------------------------------

class DgnWordsRule(RecognitionAnalysisRule):
    """
        >>> tester = ElementTester(RuleRef(DgnWordsRule()))
        >>> print(tester.recognize("words hello"))
        Recognition: "words hello"
        Word and rule pairs:
         - words (1)
         - hello (3)
        Extras:
         - dgnwords: [u'hello']

        >>> print(tester.recognize("words hello world"))
        RecognitionFailure

        >>> print(tester.recognize("words"))
        RecognitionFailure

    """

    spec   = "words <dgnwords>"
    extras = [DgnImported("dgnwords")]


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
