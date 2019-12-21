"""
Tests for the Kaldi engine

Most engine functionality is tested here, although the tests are done
entirely via `mimic`, so there are some things which have to be tested
manually.

These tests assume that the `kaldi_model` model is used.

Adapted from `test_engine_sphinx.py`.
"""

import unittest

import logging

from dragonfly.engines import (EngineBase, EngineError, MimicFailure, get_engine)
from dragonfly.grammar.elements import Literal, Sequence, ListRef
from dragonfly.grammar.list import List
from dragonfly.grammar.grammar_base import Grammar
from dragonfly.grammar.rule_base import Rule
from dragonfly.grammar.recobs import RecognitionObserver
from dragonfly.grammar.rule_compound import CompoundRule
from dragonfly.test import (ElementTester, RuleTestGrammar)

try:
    from dragonfly.engines.backend_kaldi.engine import KaldiError
except ImportError:
    KaldiError = Exception


class MockLoggingHandler(logging.Handler):
    """
    Mock logging handler to check for expected logs.
    Adapted this from a Stack Overflow answer: https://stackoverflow.com/a/1049375
    """

    def __init__(self, *args, **kwargs):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())


class RecognitionObserverTester(RecognitionObserver):
    """ RecognitionObserver class from the recobs doctests. """

    def __init__(self):
        RecognitionObserver.__init__(self)
        self.waiting = False
        self.words = None

    def on_begin(self):
        self.waiting = True
        self.words = None

    def on_recognition(self, words):
        self.waiting = False
        self.words = words

    def on_failure(self):
        self.waiting = False
        self.words = False


class KaldiEngineCase(unittest.TestCase):
    """
    Base TestCase class for Kaldi engine tests
    """

    log = logging.getLogger("engine")

    def setUp(self):
        self.engine = get_engine("kaldi")

        # Map for test functions
        self.test_map = {}

        # Connect the engine.
        self.engine.connect()

        # Register a recognition observer.
        self.test_recobs = RecognitionObserverTester()
        self.test_recobs.register()

    def tearDown(self):
        self.test_map.clear()
        self.test_recobs.unregister()
        self.engine.disconnect()

    # ---------------------------------------------------------------------
    # Methods for control-flow assertion.

    def get_test_function(self):
        """
        Create and return a test function used for testing whether
        key phrases or rules are processed correctly, insofar as they reach
        the correct processing method/function.

        Note that returned test functions accept variable arguments.
        :return: callable
        """
        def func(*_):
            # Function was reached
            try:
                self.test_map[id(func)] += 1
            except KeyError:
                # Ignore any key errors; if this function's id is not in
                # test_map, then it's not relevant to the currently running
                # test method.
                pass

        self.test_map[id(func)] = 0
        return func

    def assert_test_function_called(self, func, n):
        """
        Assert that a test function was called n times.
        :type func: callable
        :param n: number of times the test function should have been called
        """
        x = self.test_map[id(func)]
        self.assertEqual(x, n, "wrapped test function was called %d time(s) "
                               "instead of %d time(s)" % (x, n))

    def reset_test_functions(self):
        """
        Reset the test_map values for all test functions.
        """
        for key in self.test_map.keys():
            self.test_map[key] = 0

    # ---------------------------------------------------------------------
    # Methods for asserting recognition success or failure.

    def assert_mimic_success(self, *phrases):
        """
        Assert that the engine can successfully mimic a number of speech
        strings.
        """
        try:
            for phrase in phrases:
                self.engine.mimic(phrase)
        except MimicFailure:
            self.fail("MimicFailure caught")

    def assert_mimic_failure(self, *phrases):
        for phrase in phrases:
            self.assertRaises(MimicFailure, self.engine.mimic, phrase)

    def assert_recobs_result(self, waiting, words):
        self.assertEqual(self.test_recobs.waiting, waiting)
        self.assertEqual(self.test_recobs.words, words)


class EngineTests(KaldiEngineCase):
    """
    Tests for most of the engine's functionality.
    """
    def test_get_engine_kaldi_is_usable(self):
        """
        Verify that the kaldi engine is usable by testing that a simple
        rule is loaded correctly and works correctly.
        """
        engine = get_engine()
        assert engine.name == "kaldi"
        assert isinstance(self.engine, EngineBase)
        engine.speak("testing kaldi")

        # Test that a basic rule can be loaded and recognized.
        seq = Sequence([Literal("hello"), Literal("world")])
        tester = ElementTester(seq, engine=engine)
        results = tester.recognize("hello world")
        self.assertEqual(results, [u"hello", u"world"])

    # FIXME: handling reseting user lexicon
    # def test_unknown_grammar_words(self):
    #     """ Verify that warnings are logged for a grammar with unknown words. """
    #     grammar = Grammar("test")
    #     grammar.add_rule(CompoundRule(name="r1", spec="testing unknownword"))
    #     grammar.add_rule(CompoundRule(name="r2", spec="wordz|morwordz"))

    #     # Catch log messages.
    #     handler = MockLoggingHandler()
    #     log = logging.getLogger("engine.compiler")
    #     log.addHandler(handler)
    #     grammar.load()
    #     log.removeHandler(handler)

    #     # Check the logged messages.
    #     warnings = handler.messages["warning"]
    #     self.assertEqual(len(warnings), 3)
    #     self.assertIn("unknownword", warnings[0])
    #     self.assertIn("wordz", warnings[1])
    #     self.assertIn("morwordz", warnings[2])
    #     self.assertNotIn("testing", '\n'.join(warnings))

    def test_reference_names_with_spaces(self):
        """ Verify that reference names with spaces are accepted. """
        lst = List("my list", ["test list"])
        grammar = Grammar("My dragonfly grammar")
        grammar.add_rule(CompoundRule(name="my rule", spec="test rule"))
        grammar.add_rule(Rule(element=ListRef("my list", lst),
                              exported=True))
        try:
            grammar.load()
            self.assert_mimic_success("test rule")
            self.assert_mimic_success("test list")
        finally:
            grammar.unload()


# ---------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
