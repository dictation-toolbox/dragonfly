"""
Tests for the CMU Pocket Sphinx engine

Most engine functionality is tested here, although the tests are done
entirely via `mimic`, so there are some things which have to be tested
manually.

These tests assume the US English pronunciation dictionary, acoustic and
language models distributed with the `pocketsphinx` Python package are used.
"""

import unittest

import logging

from dragonfly.engines import (EngineBase, EngineError, MimicFailure,
                               get_engine)
from dragonfly.grammar.elements import Literal, Sequence, ListRef
from dragonfly.grammar.list import List
from dragonfly.grammar.grammar_base import Grammar
from dragonfly.grammar.rule_base import Rule
from dragonfly.grammar.recobs import RecognitionObserver
from dragonfly.grammar.rule_compound import CompoundRule
from dragonfly.test import (ElementTester, RuleTestGrammar)


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


class SphinxEngineCase(unittest.TestCase):
    """
    Base TestCase class for Sphinx engine tests
    """

    log = logging.getLogger("engine")
    compile_log = logging.getLogger("engine.compiler")

    def setUp(self):
        self.engine = get_engine("sphinx")

        # Ensure the relevant configuration values are used.
        self.engine.config.LANGUAGE = "en"

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

    #-----------------------------------------------------------------------
    # Methods for control-flow assertion.

    def get_test_function(self):
        """
        Create and return a test function used for testing whether rules are
        processed correctly, insofar as they reach the correct processing
        method/function.

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
        for key in self.test_map.keys(): self.test_map[key] = 0

    # ---------------------------------------------------------------------
    # Methods for asserting recognition success or failure.

    def assert_mimic_success(self, *phrases):
        """
        Assert that the engine can successfully mimic a number of speech
        strings.
        """
        try:
            for phrase in phrases: self.engine.mimic(phrases)
        except MimicFailure:
            self.fail("MimicFailure caught")

    def assert_mimic_failure(self, *phrases):
        for phrase in phrases:
            self.assertRaises(MimicFailure, self.engine.mimic, phrase)

    def assert_recobs_result(self, waiting, words):
        self.assertEqual(self.test_recobs.waiting, waiting)
        self.assertEqual(self.test_recobs.words, words)


class EngineTests(SphinxEngineCase):
    """
    Tests for most of the engine's functionality.
    """
    def test_get_engine_sphinx_is_usable(self):
        """
        Verify that the sphinx engine is usable by testing that a simple
        rule is loaded correctly and works correctly.
        """
        engine = get_engine()
        assert engine.name == "sphinx"
        assert isinstance(self.engine, EngineBase)
        engine.speak("testing sphinx")

        # Test that a basic rule can be loaded and recognized.
        seq = Sequence([Literal("hello"), Literal("world")])
        tester = ElementTester(seq, engine=engine)
        results = tester.recognize("hello world")
        self.assertEqual(results, [u"hello", u"world"])

    def test_engine_config(self):
        """ Verify that engine configuration is validated correctly. """
        options = [
            "DECODER_CONFIG",
            "LANGUAGE",

            "CHANNELS",
            "RATE",
            "SAMPLE_WIDTH",
            "BUFFER_SIZE",
        ]

        class TestConfig(object):
            pass

        # Set TestConfig values using the engine config.
        original_config = self.engine.config
        for name in options:
            setattr(TestConfig, name, getattr(original_config, name))

        def set_config(value):
            self.engine.config = value

        # Test that options are set to default values if deleted.
        # Don't compare decoder config objects with assertEqual because they
        # aren't comparable.
        for name in options:
            delattr(TestConfig, name)
            set_config(TestConfig)
            self.assertTrue(hasattr(TestConfig, name),
                            "%s was not reset" % name)
            if name != "DECODER_CONFIG":
                self.assertEqual(getattr(TestConfig, name),
                                 getattr(original_config, name),
                                 "%s did not match" % name)

    def test_unknown_grammar_words(self):
        """ Verify that warnings are logged for grammars with unknown words.
        """
        grammar = Grammar("test")
        grammar.add_rule(CompoundRule(name="r1", spec="testing unknownword"))
        grammar.add_rule(CompoundRule(name="r2", spec="wordz|natlink"))

        # Test with a list too.
        lst = List("lst", ["anotherunknownword", "testing multiplewords"])
        grammar.add_rule(CompoundRule(name="r3", spec="<lst>",
                                      extras=[ListRef("lst", lst)]))

        # Catch log messages and make some assertions.
        handler = MockLoggingHandler()
        self.compile_log.addHandler(handler)
        try:
            grammar.load()
            self.assertTrue(grammar.loaded)

            # Check the logged messages.
            warnings = handler.messages["warning"]
            self.assertEqual(len(warnings), 1)
            self.assertNotIn("testing", warnings[0])
            unknown_words = ["natlink", "unknownword", "anotherunknownword",
                             "wordz", "multiplewords"]
            for word in unknown_words:
                self.assertIn(word, warnings[0])

            # Test that list updates also produce warnings.
            lst.extend(("hello", "onemoreunknownword"))
            self.assertEqual(len(warnings), 2)
            self.assertNotIn("hello", warnings[1])
            self.assertIn("onemoreunknownword", warnings[1])
        finally:
            self.compile_log.removeHandler(handler)
            grammar.unload()

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
