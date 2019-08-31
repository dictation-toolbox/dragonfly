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
        self.engine.config.TRAINING_DATA_DIR = ""
        self.engine.config.START_ASLEEP = False
        self.engine.config.WAKE_PHRASE = "wake up"
        self.engine.config.SLEEP_PHRASE = "go to sleep"
        self.engine.config.START_TRAINING_PHRASE = "start training session"
        self.engine.config.END_TRAINING_PHRASE = "end training session"
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
        self.engine.resume_recognition()
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
            self.engine.mimic_phrases(*phrases)
        except MimicFailure:
            self.fail("MimicFailure caught")

    def assert_mimic_failure(self, *phrases):
        self.assertRaises(MimicFailure, self.engine.mimic_phrases, *phrases)

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
        # Use START_ASLEEP=True for this test.
        self.engine.config.START_ASLEEP = True
        options = [
            "DECODER_CONFIG",
            "LANGUAGE",

            "START_ASLEEP",
            "WAKE_PHRASE",
            "WAKE_PHRASE_THRESHOLD",
            "SLEEP_PHRASE",
            "SLEEP_PHRASE_THRESHOLD",

            "TRAINING_DATA_DIR",
            "TRANSCRIPT_NAME",
            "START_TRAINING_PHRASE",
            "START_TRAINING_PHRASE_THRESHOLD",
            "END_TRAINING_PHRASE",
            "END_TRAINING_PHRASE_THRESHOLD",

            "CHANNELS",
            "RATE",
            "SAMPLE_WIDTH",
            "FRAMES_PER_BUFFER",
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

    def test_pause_resume_recognition(self):
        """ Verify that pause/resume recognition functionality works. """

        grammar = RuleTestGrammar("test1")
        grammar.add_rule(CompoundRule(name="r1", spec="hello world"))

        def assert_recognize_succeeds():
            results = grammar.recognize_node("hello world").words()
            assert results == ["hello", "world"]

        # Enter sleep mode.
        self.engine.pause_recognition()
        self.assertTrue(self.engine.recognition_paused)

        # Mimicking hello world should succeed when recognition is
        # paused, but it will not succeed when actually speaking.
        assert_recognize_succeeds()

        # Check that recognition still succeeds when recognition is
        # resumed again.
        self.engine.resume_recognition()
        self.assertFalse(self.engine.recognition_paused)
        assert_recognize_succeeds()

        # Test that mimicking wake and sleep phrases also works
        # correctly.
        self.assert_mimic_success("go to sleep")
        self.assertTrue(self.engine.recognition_paused)
        self.assert_mimic_success("wake up")
        self.assertFalse(self.engine.recognition_paused)

    def test_start_asleep(self):
        """ Verify that the START_ASLEEP config option works. """
        # config.START_ASLEEP is False for the tests by default, so test
        # that first.
        self.assertFalse(self.engine.recognition_paused)
        self.assert_mimic_success("go to sleep")

        # Now set it to True, restart the engine and test again.
        self.engine.config.START_ASLEEP = True
        self.engine.disconnect()
        self.engine.connect()
        self.assertTrue(self.engine.recognition_paused)
        self.assert_mimic_success("wake up")

    def test_keyphrases_and_recobs(self):
        """ Verify that observers are notified of keyphrase events. """
        test1 = self.get_test_function()
        test2 = self.get_test_function()

        # Register two key phrases
        self.engine.set_keyphrase("hello world", 1e-20, test1)
        self.engine.set_keyphrase("testing testing", 1e-30, test2)

        def assert_success():
            self.assert_mimic_success("hello world")
            self.assert_recobs_result(False, (u"hello", u"world"))
            self.assert_test_function_called(test1, 1)
            self.assert_mimic_success("testing testing")
            self.assert_recobs_result(False, (u"testing", u"testing"))
            self.assert_test_function_called(test2, 1)
            self.reset_test_functions()

        # Test that both key phrases can be mimicked and that the observer
        # was notified.
        assert_success()

        # Test that both key phrases can be mimicked in sleep mode.
        self.engine.pause_recognition()
        assert_success()
        self.engine.resume_recognition()

        # Test that removed key phrases no longer match
        self.engine.unset_keyphrase("hello world")
        self.assert_mimic_failure("hello world")
        self.assert_recobs_result(False, False)
        self.assert_test_function_called(test1, 0)
        self.engine.unset_keyphrase("testing testing")
        self.assert_mimic_failure("testing testing")
        self.assert_recobs_result(False, False)
        self.assert_test_function_called(test1, 0)

    def test_set_keyphrase_unknown_words(self):
        """ Verify that setting a keyphrase with an unknown word raises an error.
        """
        from dragonfly.engines.backend_sphinx.engine import UnknownWordError
        self.assertRaises(UnknownWordError, self.engine.set_keyphrase,
                          "notaword", 1e-20, lambda: None)

    def test_built_in_keyphrase_unknown_words(self):
        """ Verify that errors are logged for built-in keyphrases with unknown words.
        """
        # Test invalid built-in keyphrases.
        self.engine.config.WAKE_PHRASE = "wake up unknownword"
        self.engine.config.SLEEP_PHRASE = "aninvalid sleepphrase"
        self.engine.config.START_TRAINING_PHRASE = "another invalidphrase"
        self.engine.config.END_TRAINING_PHRASE = "end trainingsession"

        # Restart the engine manually to verify that errors are logged for
        # the keyphrases on connect().
        handler = MockLoggingHandler()
        self.log.addHandler(handler)
        try:
            self.engine.disconnect()
            self.engine.connect()
        finally:
            self.log.removeHandler(handler)

        # Check the logged messages. Each of the unknown words in all four
        # built-in keyphrases should be listed in separate messages.
        errors = handler.messages["error"]
        self.assertEqual(len(errors), 4)
        self.assertIn("unknownword", errors[0])
        self.assertIn("aninvalid", errors[1])
        self.assertIn("sleepphrase", errors[1])
        self.assertIn("invalidphrase", errors[2])
        self.assertIn("trainingsession", errors[3])

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

    def test_training_session(self):
        """ Verify that no recognition processing occurs when training. """
        # Set up a rule to "train".
        test = self.get_test_function()

        class TestRule(CompoundRule):
            spec = "test training"
            _process_recognition = test

        # Create and load a grammar with the rule.
        grammar = Grammar("test")
        grammar.add_rule(TestRule())
        grammar.load()
        try:
            # Start a training session.
            self.engine.start_training_session()

            # Test that mimic succeeds, no processing occurs, and the
            # observer is still notified of events.
            self.assert_mimic_success("test training")
            self.assert_test_function_called(test, 0)
            self.assert_recobs_result(False, (u"test", u"training"))

            # End the session and test again.
            self.engine.end_training_session()
            self.assert_mimic_success("test training")
            self.assert_test_function_called(test, 1)
            self.assert_recobs_result(False, (u"test", u"training"))
        finally:
            grammar.unload()


# ---------------------------------------------------------------------


if __name__ == '__main__':
    unittest.main()
