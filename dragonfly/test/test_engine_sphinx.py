"""
Tests for the CMU Pocket Sphinx engine

Most engine functionality is tested here, although the tests are done entirely
via `mimic`, so there are some things which have to be tested manually for the
moment.

These tests assume the US English pronunciation dictionary, acoustic and language
models distributed with the `pocketsphinx` Python package are used.
"""

import unittest

import time
import logging

from sphinxwrapper import DefaultConfig

from dragonfly import *
from dragonfly import List as DragonflyList, DictList as DragonflyDict
from dragonfly.engines.backend_sphinx.engine import SphinxEngine


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


class TestContext(Context):
    def __init__(self, active):
        super(TestContext, self).__init__()
        self.active = active

    def matches(self, executable, title, handle):
        # Ignore the parameters and return self.active.
        return self.active


class SphinxEngineCase(unittest.TestCase):
    """
    Base TestCase class for Sphinx engine tests
    """
    def setUp(self):
        engine = get_engine("sphinx")
        assert isinstance(engine, SphinxEngine)
        assert engine.name == "sphinx"
        self.engine = engine

        # Save current config
        self.engine_config = self.engine.config

        # Set a default NEXT_PART_TIMEOUT value so there aren't weird timing errors
        # that break tests. Value of 0 means no timeout at all.
        self.engine.config.NEXT_PART_TIMEOUT = 0

        # Set training data directory to None for the tests.
        self.engine.config.TRAINING_DATA_DIR = None

        # Ensure the relevant default configuration values are used
        self.engine.config.START_ASLEEP = False
        self.engine.config.WAKE_PHRASE = "wake up"
        self.engine.config.SLEEP_PHRASE = "go to sleep"
        self.engine.config.START_TRAINING_PHRASE = "start training session"
        self.engine.config.END_TRAINING_PHRASE = "end training session"
        self.engine.config.LANGUAGE = "en"

        # Map for test functions
        self.test_map = {}

        # Add a logging handler.
        self.logging_handler = MockLoggingHandler()
        self.engine.log.addHandler(self.logging_handler)

        # Connect the engine.
        engine.connect()

    def tearDown(self):
        # Restore saved config and do some other things.
        self.engine.config = self.engine_config
        self.engine.disconnect()
        self.test_map.clear()
        self.engine.log.removeHandler(self.logging_handler)

    # ---------------------------------------------------------------------
    # Methods for control-flow assertion.

    def get_test_function(self):
        """
        Create and return a test function used for testing whether rules are
        processed correctly, insofar as they reach the correct processing method.

        Note that returned test functions accept variable arguments.
        :return: callable
        """
        def func(*args):
            # Function was reached
            try:
                self.test_map[id(func)] += 1
            except KeyError:
                # Ignore any key errors; if this function's id is not in test_map,
                # then it's not relevant to the currently running test method.
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
    # Methods for asserting mimic success or failure

    def assert_mimic_success(self, *phrases):
        """
        Assert that the engine can successfully mimic a number of speech strings,
        or fail with the provided error message.
        """
        try:
            self.engine.mimic_phrases(*phrases)
        except MimicFailure:
            self.fail("MimicFailure caught")

    def assert_mimic_failure(self, *phrases):
        self.assertRaises(MimicFailure, self.engine.mimic_phrases, *phrases)


class BasicEngineTests(SphinxEngineCase):
    """
    Tests for basic engine functionality.
    """
    def test_get_engine_sphinx_is_usable(self):
        """
        Verify that the sphinx engine is usable by testing that a simple
        rule is loaded correctly and works correctly.
        """
        test = self.get_test_function()

        class TestRule(CompoundRule):
            spec = "hello world"
            _process_recognition = test

        g = Grammar("test1")
        g.add_rule(TestRule())
        g.load()
        self.assertTrue(g.loaded)
        self.assert_mimic_success("hello world")
        self.assert_test_function_called(test, 1)

    def test_engine_config(self):
        """
        Test whether engine configuration is validated correctly.
        """

        # Required config names
        required = [
            "DECODER_CONFIG",
            "LANGUAGE",
            "PYAUDIO_STREAM_KEYWORD_ARGS",
            "NEXT_PART_TIMEOUT",
            "START_ASLEEP",
            "WAKE_PHRASE",
            "SLEEP_PHRASE",
            "WAKE_PHRASE_THRESHOLD",
            "SLEEP_PHRASE_THRESHOLD",
            "TRAINING_DATA_DIR",
            "START_TRAINING_PHRASE",
            "START_TRAINING_THRESHOLD",
            "END_TRAINING_PHRASE",
            "END_TRAINING_THRESHOLD",
        ]

        class TestConfig(object):
            DECODER_CONFIG = DefaultConfig()
            LANGUAGE = "en"
            PYAUDIO_STREAM_KEYWORD_ARGS = {}
            NEXT_PART_TIMEOUT = 0
            START_ASLEEP = False
            WAKE_PHRASE = "wake up"
            WAKE_PHRASE_THRESHOLD = 1e-20
            SLEEP_PHRASE = "go to sleep"
            SLEEP_PHRASE_THRESHOLD = 1e-40
            TRAINING_DATA_DIR = None
            START_TRAINING_PHRASE = "start training session"
            START_TRAINING_THRESHOLD = 1e-48
            END_TRAINING_PHRASE = "end training session"
            END_TRAINING_THRESHOLD = 1e-45

        def set_config(value):
            self.engine.config = value

        # Test with correct attributes
        self.assertIsNone(set_config(TestConfig))

        # Delete each attribute and check that an EngineError is raised upon
        # setting the config again.
        for name in required:
            delattr(TestConfig, name)
            self.assertRaises(EngineError, set_config, TestConfig)

    def test_load_unload(self):
        """
        Test that grammars are properly loaded and unloaded.
        """
        grammar = Grammar("test")
        # Add the simplest rule and test that it loads and unloads correctly
        rule1 = CompoundRule("rule1", "hello")
        grammar.add_rule(rule1)
        grammar.load()
        self.assertTrue(grammar.loaded)
        self.assert_mimic_success("hello")
        grammar.unload()
        self.assertFalse(grammar.loaded)
        self.assert_mimic_failure("hello")

        # Test that a dependent rule is unloaded correctly.
        rule2 = CompoundRule("rule2", "<rule1ref> there",
                             extras=[RuleRef(rule1, name="rule1ref")])
        grammar.add_rule(rule2)
        grammar.load()
        self.assertTrue(grammar.loaded)
        self.assert_mimic_success("hello there")
        grammar.unload()
        self.assertFalse(grammar.loaded)
        self.assert_mimic_failure("hello there")

    def test_mapping_rule(self):
        """
        Test that the engine can handle a grammar with a MappingRule.
        """
        # Get two test functions for the rules to use
        test1 = self.get_test_function()
        test2 = self.get_test_function()

        class TestRule(MappingRule):
            mapping = {
                "hello": Function(test1),
                "hi": Function(test2),
            }

        g = Grammar("test")
        g.add_rule(TestRule())
        g.load()
        self.assertTrue(g.loaded)

        # Test 'hello' rule works and that only the test1 function was called
        self.assert_mimic_success("hello")
        self.assert_test_function_called(test1, 1)
        self.assert_test_function_called(test2, 0)
        # Reset test functions
        self.reset_test_functions()

        # Test 'hi' rule works and that only the test2 function was called
        self.assert_mimic_success("hi")
        self.assert_test_function_called(test1, 0)
        self.assert_test_function_called(test2, 1)

    def test_update_list(self):
        """
        Test support for dragonfly lists.
        """
        # Set up a new list and add an item
        fruit_list = DragonflyList("fruit")
        fruit_list.append("apple")
        fruit_list_ref = ListRef("fruit_ref", fruit_list)

        # Load a new grammar with a rule referencing the fruit list
        grammar = Grammar("test")
        r = Rule("fav_fruit", fruit_list_ref, exported=True)
        grammar.add_rule(r)
        grammar.load()
        self.assertTrue(grammar.loaded)

        self.assert_mimic_success("apple")

        # Try updating the list
        fruit_list.append("banana")
        self.assertListEqual(["apple", "banana"], r.element.list)

        # If mimic fails, then the list wasn't updated correctly.
        self.assert_mimic_success("banana")

    def test_update_list_dict(self):
        """
        Test support for dragonfly dict lists.
        """
        # Set up a new dict list and add an item
        fruit_dict = DragonflyDict("fruit_dict")
        fruit_dict["mango"] = "nope"

        # Add a new rule to the grammar using a DictListRef element and load it
        grammar = Grammar("test")
        r = Rule("fruits", DictListRef("fruit_dict_ref", fruit_dict),
                 exported=True)
        grammar.add_rule(r)
        grammar.load()
        self.assertTrue(grammar.loaded)

        self.assert_mimic_success("mango")

        # Try updating the list
        fruit_dict["mandarin"] = "yep"
        self.assertDictEqual({"mango": "nope", "mandarin": "yep"}, r.element.list)

        # If mimic fails, then the dict list wasn't updated correctly.
        self.assert_mimic_success("mandarin")

    def test_choices(self):
        """
        Test that a dragonfly rule using a Choice extra works correctly.
        """
        test = self.get_test_function()
        digits_dict = {
            "one": "1",
            "two": "2",
            "three": "3",
            "four": "4",
            "five": "5",
            "six": "6",
            "seven": "7",
            "eight": "8",
            "nine": "9",
            "point": ".",
        }

        class TestRule(CompoundRule):
            spec = "<digits>"
            extras = [Choice("digits", digits_dict)]
            _process_recognition = test

        g = Grammar("test")
        g.add_rule(TestRule())
        g.load()
        self.assertTrue(g.loaded)

        # Test that all choices are processed correctly
        for i, phrase in enumerate(["one", "two", "three", "four", "five", "six",
                                    "seven", "eight", "nine", "point"]):
            self.assert_mimic_success(phrase)
            self.assert_test_function_called(test, i+1)  # starting at 1, not 0.

    def test_recognition_history(self):
        observer = RecognitionHistory()
        observer.register()
        self.assertListEqual(observer, [])  # RecognitionHistory is a list subclass

        # Set up a test grammar and rule
        g = Grammar("test")
        g.add_rule(CompoundRule("rule1", "testing"))
        g.load()
        self.assertTrue(g.loaded)

        self.assert_mimic_success("testing")
        self.assertListEqual(observer, [[("testing", 0)]])

    def test_name_conflict(self):
        """
        Test whether the engine correctly handles rules with the same name, but
        different elements.
        """
        g1 = Grammar("test1")
        g2 = Grammar("test2")
        g1.add_rule(CompoundRule(name="rule", spec="test"))
        g2.add_rule(CompoundRule(name="rule", spec="testing"))

        g1.load()
        self.assertTrue(g1.loaded)
        g2.load()
        self.assertTrue(g2.loaded)
        self.assert_mimic_success("test")
        self.assert_mimic_success("testing")

    def test_same_rule_in_different_grammars(self):
        g1 = Grammar("test1")
        g2 = Grammar("test2")

        test1 = self.get_test_function()
        test2 = self.get_test_function()

        class Rule1(CompoundRule):
            spec = "test"
            _process_recognition = test1

        class Rule2(CompoundRule):
            spec = "test"
            _process_recognition = test2

        # Add and load the rules
        g1.add_rule(Rule1())
        g2.add_rule(Rule2())
        g1.load()
        self.assertTrue(g1.loaded)
        g2.load()
        self.assertTrue(g2.loaded)

        self.assert_mimic_success("test")

        # Check that only one of these rules was processed
        self.assert_test_function_called(test1, 1)
        self.assert_test_function_called(test2, 0)

    def test_pause_resume_recognition(self):
        test = self.get_test_function()

        class TestRule(CompoundRule):
            spec = "hello world"
            _process_recognition = test

        g = Grammar("test1")
        g.add_rule(TestRule())
        g.load()
        self.assertTrue(g.loaded)
        self.assertFalse(self.engine.recognition_paused)

        # Mimicking hello world should fail *silently* when recognition is paused
        self.engine.pause_recognition()
        self.assertTrue(self.engine.recognition_paused)
        self.engine.mimic("hello world")  # note this is *not* a recognition failure
        self.assert_test_function_called(test, 0)
        self.engine.resume_recognition()
        self.assertFalse(self.engine.recognition_paused)
        self.assert_mimic_success("hello world")
        self.assert_test_function_called(test, 1)

        # Test again mimicking wake and sleep phrases
        self.assert_mimic_success("go to sleep")
        self.assertTrue(self.engine.recognition_paused)
        self.engine.mimic("hello world")
        self.assert_test_function_called(test, 1)  # no change
        self.assert_mimic_success("wake up")
        self.assertFalse(self.engine.recognition_paused)
        self.assert_mimic_success("hello world")
        self.assert_test_function_called(test, 2)

    def test_rule_contexts(self):
        # Test that rules with contexts work and that rules with context=None still
        # work regardless of context.
        test1, test2 = self.get_test_function(), self.get_test_function()
        rule1 = MappingRule(name="test1", mapping={"test global": Function(test1)})
        context = TestContext(True)
        rule2 = MappingRule(
            name="test2", mapping={"test context": Function(test2)},
            context=TestContext(True)
        )

        # Create and load a grammar.
        grammar = Grammar("test")
        grammar.add_rule(rule1)
        grammar.add_rule(rule2)
        grammar.load()

        # Test that both rules rules work.
        self.assert_mimic_success("test context")
        self.assert_mimic_success("test global")
        self.assert_test_function_called(test1, 1)
        self.assert_test_function_called(test2, 1)

        # Go out of context and test both rules again.
        context.active = False
        self.assert_mimic_failure("test context")
        self.assert_mimic_success("test global")
        self.assert_test_function_called(test1, 2)
        self.assert_test_function_called(test2, 1)

        # Try again in-context.
        context.active = True
        self.assert_mimic_success("test context")
        self.assert_mimic_success("test global")
        self.assert_test_function_called(test1, 3)
        self.assert_test_function_called(test2, 2)

    def test_grammar_contexts(self):
        # Test that grammars with contexts work and that global contexts still work
        # regardless of context.
        test1, test2 = self.get_test_function(), self.get_test_function()

        class TestRule1(MappingRule):
            mapping = {"test global": Function(test1)}

        class TestRule2(MappingRule):
            mapping = {"test context": Function(test2)}

        # Create and load a global grammar.
        grammar1 = Grammar("global")
        grammar1.add_rule(TestRule1())
        grammar1.load()

        # Create and load a grammar using a context.
        context = TestContext(active=True)
        grammar2 = Grammar("context", context=context)
        grammar2.add_rule(TestRule2())
        grammar2.load()

        # Test that rules in both grammars work.
        self.assert_mimic_success("test context")
        self.assert_mimic_success("test global")
        self.assert_test_function_called(test1, 1)
        self.assert_test_function_called(test2, 1)

        # Go out of context and test both rules again.
        context.active = False
        self.assert_mimic_failure("test context")
        self.assert_mimic_success("test global")
        self.assert_test_function_called(test1, 2)
        self.assert_test_function_called(test2, 1)

        # Try again in-context.
        context.active = True
        self.assert_mimic_success("test context")
        self.assert_mimic_success("test global")
        self.assert_test_function_called(test1, 3)
        self.assert_test_function_called(test2, 2)

    def test_start_asleep(self):
        # config.START_ASLEEP is False for the tests by default, so test that first.
        self.assertFalse(self.engine.recognition_paused)
        self.assert_mimic_success("go to sleep")

        # Now set it to True, restart the engine and test again.
        self.engine.config.START_ASLEEP = True
        self.engine.disconnect()
        self.engine.connect()
        self.engine.post_loader_init()  # used instead of 'recognise_forever' here
        self.assertTrue(self.engine.recognition_paused)
        self.assert_mimic_success("wake up")

    def test_key_phrases(self):
        """
        Test key phrase functionality and observer notify methods.
        """
        test1 = self.get_test_function()
        test2 = self.get_test_function()
        on_begin_test = self.get_test_function()
        on_recognition_test = self.get_test_function()
        on_failure_test = self.get_test_function()

        # Set up a custom observer using test methods
        class TestObserver(RecognitionObserver):
            on_begin = on_begin_test
            on_recognition = on_recognition_test
            on_failure = on_failure_test

        self.engine.register_recognition_observer(TestObserver())

        # Register two key phrases
        self.engine.set_keyphrase("hello world", 1e-20, test1)
        self.engine.set_keyphrase("testing testing", 1e-30, test2)

        # Test that both key phrases can be mimicked
        self.assert_mimic_success("hello world")
        self.assert_test_function_called(test1, 1)
        self.assert_test_function_called(on_begin_test, 1)
        self.assert_test_function_called(on_recognition_test, 1)
        self.assert_mimic_success("testing testing")
        self.assert_test_function_called(test2, 1)
        self.assert_test_function_called(on_begin_test, 2)
        self.assert_test_function_called(on_recognition_test, 2)
        self.assert_test_function_called(on_failure_test, 0)

        # Test that neither of the key phrases match when recognition is paused
        self.engine.pause_recognition()
        self.engine.mimic("hello world")
        self.assert_test_function_called(test1, 1)  # no change
        self.engine.mimic("testing testing")
        self.assert_test_function_called(test2, 1)  # no change

        # Test that no notify test functions have been called again
        self.assert_test_function_called(on_begin_test, 2)
        self.assert_test_function_called(on_recognition_test, 2)
        self.assert_test_function_called(on_failure_test, 0)

        # Resume recognition again. on_recognition_test should have been called.
        self.engine.resume_recognition()
        self.assert_test_function_called(on_recognition_test, 3)

        # Test that removed key phrases no longer match
        self.engine.unset_keyphrase("hello world")
        self.assert_mimic_failure("hello world")
        self.assert_test_function_called(test1, 1)  # no change
        self.assert_test_function_called(on_begin_test, 3)
        self.assert_test_function_called(on_failure_test, 1)
        self.engine.unset_keyphrase("testing testing")
        self.assert_mimic_failure("testing testing")
        self.assert_test_function_called(test2, 1)  # no change
        self.assert_test_function_called(on_begin_test, 4)
        self.assert_test_function_called(on_failure_test, 2)

    def test_unknown_keyphrase_words(self):
        # Test that keyphrases with unknown words log appropriate error messages.
        self.engine.set_keyphrase("notaword", 1e-20, lambda: None)
        self.assertEqual(
            self.logging_handler.messages["error"][0],
            "keyphrase used words not found in the pronunciation dictionary: "
            "notaword"
        )

        # Test invalid built-in keyphrases.
        self.engine.config.WAKE_PHRASE = "wake up unknownword"
        self.engine.config.SLEEP_PHRASE = "aninvalid sleepphrase"
        self.engine.config.START_TRAINING_PHRASE = "another invalidphrase"
        self.engine.config.END_TRAINING_PHRASE = "end trainingsession"

        # Restart the engine manually to verify that an error is logged for the
        # keyphrases on connect().
        self.engine.disconnect()
        self.engine.connect()

        # Check the logged messages. Each of the unknown words in all four
        # built-in keyphrases should be listed.
        self.assertEqual(
            self.logging_handler.messages["error"][1],
            "keyphrase used words not found in the pronunciation dictionary: "
            "aninvalid, invalidphrase, sleepphrase, trainingsession, unknownword"
        )

    def test_unknown_grammar_words(self):
        # Test that grammars using unknown words log appropriate error messages when
        # they fail to load.
        class TestRule1(CompoundRule):
            spec = "testing unknownword"

        class TestRule2(MappingRule):
            mapping = {
                "wordz": ActionBase(),
                "natlink": ActionBase()
            }

        g = Grammar("test")
        g.add_rule(TestRule1())
        g.add_rule(TestRule2())
        g.load()

        # Check the logged messages. The words should be in alphabetical order.
        self.assertEqual(
            self.logging_handler.messages["error"][0],
            "grammar 'test' used words not found in the pronunciation dictionary: "
            "natlink, unknownword, wordz"
        )

    def test_training_session(self):
        # Test that no recognition processing is done when a training session is
        # active.

        # Set up a rule to "train".
        test = self.get_test_function()

        class TestRule(CompoundRule):
            spec = "test training"
            _process_recognition = test

        # Create and load a grammar with the rule.
        grammar = Grammar("test")
        grammar.add_rule(TestRule())
        grammar.load()

        # Set up a custom observer using test methods
        on_begin_test = self.get_test_function()
        on_recognition_test = self.get_test_function()
        on_failure_test = self.get_test_function()

        class TestObserver(RecognitionObserver):
            on_begin = on_begin_test
            on_recognition = on_recognition_test
            on_failure = on_failure_test

        self.engine.register_recognition_observer(TestObserver())

        # Start a training session.
        self.engine.start_training_session()

        # Test that mimic succeeds, no processing occurs, and the TestObserver
        # is still notified of events.
        self.assert_mimic_success("test training")
        self.assert_test_function_called(test, 0)
        self.assert_test_function_called(on_begin_test, 1)
        self.assert_test_function_called(on_recognition_test, 1)
        self.assert_test_function_called(on_failure_test, 0)

        # End the session and test again.
        self.engine.end_training_session()
        self.assert_mimic_success("test training")
        self.assert_test_function_called(test, 1)
        self.assert_test_function_called(on_begin_test, 2)
        self.assert_test_function_called(on_recognition_test, 2)
        self.assert_test_function_called(on_failure_test, 0)


class DictationEngineTests(SphinxEngineCase):
    """
    Tests for the engine's dictation functionality.
    """
    def test_single_dictation(self):
        """
        Test that the engine can handle a dragonfly rule using a Dictation element.
        """
        test = self.get_test_function()

        class TestRule(MappingRule):
            mapping = {"<dictation>": Function(test)}
            extras = [Dictation("dictation")]

        g = Grammar("test")
        g.add_rule(TestRule())
        g.load()
        self.assertTrue(g.loaded)
        self.assert_mimic_success("hello")
        self.assert_test_function_called(test, 1)

        # Test that it works again
        self.assert_mimic_success("hello")
        self.assert_test_function_called(test, 2)

        # Test again with multiple words
        self.assert_mimic_success("hello world")
        self.assert_test_function_called(test, 3)

    def test_dictation_with_other_elements(self):
        """
        Test that the engine can handle dragonfly rules using dictation with other
        elements.

        This is being tested because the way dictation works for this engine is
        different than how the other engines handle it: Sphinx needs utterance
        pauses between grammar and dictation rule parts.
        """
        test1 = self.get_test_function()
        test2 = self.get_test_function()

        class TestRule(MappingRule):
            mapping = {
                "hello <dictation>": Function(test1),
                "<dictation> testing": Function(test2),
            }
            extras = [Dictation("dictation")]

        g = Grammar("test")
        g.add_rule(TestRule())
        g.load()
        self.assertTrue(g.loaded)

        # Dictation and other elements are processed separately with pauses
        self.assert_mimic_success("hello", "world")  # test mapping 1
        self.assert_test_function_called(test1, 1)
        self.assert_test_function_called(test2, 0)

        # Test with mapping 2
        self.assert_mimic_success("testing", "testing")

        # Test that it works again with mapping 1
        self.reset_test_functions()
        self.assert_mimic_success("hello", "world")
        self.assert_test_function_called(test1, 1)
        self.assert_test_function_called(test2, 0)

        # Test with mapping 2 again
        self.reset_test_functions()
        self.assert_mimic_success("test", "testing")
        self.assert_test_function_called(test1, 0)
        self.assert_test_function_called(test2, 1)

        # Test again with multiple words
        self.reset_test_functions()
        self.assert_mimic_success("hello", "hi there")
        self.assert_test_function_called(test1, 1)
        self.assert_test_function_called(test2, 0)

        # And test again using mapping 2
        self.reset_test_functions()
        self.assert_mimic_success("test test test", "testing")
        self.assert_test_function_called(test2, 1)
        self.assert_test_function_called(test1, 0)

        # Test incomplete sequences
        self.reset_test_functions()
        self.assert_mimic_success("hello")  # start of mapping one
        self.assert_test_function_called(test1, 0)  # incomplete sequence
        self.assert_mimic_success("test", "testing")
        self.assert_test_function_called(test1, 1)  # mapping one completely matched
        # mapping two only partially matched with <dictation> as "testing"
        self.assert_test_function_called(test2, 0)

    def test_recognition_observer(self):
        """
        Test that the engine's recognition observer manager works correctly.
        """
        on_begin_test = self.get_test_function()
        on_recognition_test = self.get_test_function()
        on_failure_test = self.get_test_function()
        on_next_rule_part_test = self.get_test_function()

        # Set up a custom observer using test methods
        class TestObserver(RecognitionObserver):
            on_begin = on_begin_test
            on_next_rule_part = on_next_rule_part_test
            on_recognition = on_recognition_test
            on_failure = on_failure_test

        # Set up a TestObserver instance and a grammar with multiple rules to use
        observer = TestObserver()
        observer.register()
        grammar = Grammar("test")
        grammar.add_rule(CompoundRule("rule1", "hello world"))
        grammar.add_rule(CompoundRule("rule2", "say <dictation>",
                                      extras=[Dictation("dictation")]))
        grammar.load()
        self.assertTrue(grammar.loaded)

        # Test that each method is called properly
        self.assert_mimic_success("hello world")

        # on_begin is called during each mimic. on_recognition should be called
        # once per successful and complete recognition. Both on_failure and
        # on_next_rule_part shouldn't have been called yet.
        self.assert_test_function_called(on_begin_test, 1)
        self.assert_test_function_called(on_recognition_test, 1)
        self.assert_test_function_called(on_failure_test, 0)
        self.assert_test_function_called(on_next_rule_part_test, 0)

        # Test with a dictation rule
        self.assert_mimic_success("say")

        # Recognition begins again, is incomplete and no failure yet.
        self.assert_test_function_called(on_begin_test, 2)
        self.assert_test_function_called(on_recognition_test, 1)
        self.assert_test_function_called(on_failure_test, 0)

        # on_next_rule_part should be called because there are more rule parts
        self.assert_test_function_called(on_next_rule_part_test, 1)

        # Test the next part of the dictation rule
        self.assert_mimic_success("testing testing")

        # Recognition begins again, is complete, and no failure yet.
        self.assert_test_function_called(on_begin_test, 3)
        self.assert_test_function_called(on_recognition_test, 2)
        self.assert_test_function_called(on_failure_test, 0)

        # on_next_rule_part shouldn't have been called because this is the last part
        # and on_recognition will be called instead
        self.assert_test_function_called(on_next_rule_part_test, 1)

        # Recognition begins again and failure occurs.
        self.assert_mimic_failure("testing")
        self.assert_test_function_called(on_begin_test, 4)
        self.assert_test_function_called(on_next_rule_part_test, 1)  # no change
        self.assert_test_function_called(on_failure_test, 1)
        self.assert_test_function_called(on_recognition_test, 2)

        # Test that using None or "" also calls the on_failure method
        self.assert_mimic_failure(None)
        self.assert_test_function_called(on_failure_test, 2)
        self.assert_mimic_failure("")
        self.assert_test_function_called(on_failure_test, 3)
        self.assert_test_function_called(on_next_rule_part_test, 1)  # no change

        # Unregister the observer
        observer.unregister()

    def test_no_hypothesis(self):
        """
        Check that if something that doesn't match any rule is mimicked, nothing
        gets recognised.
        """
        test1 = self.get_test_function()
        test2 = self.get_test_function()

        class TestRule(MappingRule):
            mapping = {
                "testing": Function(test1),
                "<dictation>": Function(test2)
            }
            extras = [Dictation("dictation")]

        g = Grammar("test")
        g.add_rule(TestRule())
        g.load()
        self.assertTrue(g.loaded)

        self.assert_mimic_failure(None)
        self.assert_test_function_called(test1, 0)
        self.assert_test_function_called(test2, 0)
        self.assert_mimic_failure("")
        self.assert_test_function_called(test1, 0)
        self.assert_test_function_called(test2, 0)
        self.assert_mimic_success("hello")
        self.assert_test_function_called(test1, 0)
        self.assert_test_function_called(test2, 1)

    def test_sequence_timeout(self):
        """
        Test that when speaking subsequent parts of rules involving Dictation
        elements, the recognition times out if there is a timeout period set.
        """
        # Set a timeout period for this test of 100 ms, which is unreasonable for
        # humans, but fine for mimic().
        timeout = 0.1
        self.engine.config.NEXT_PART_TIMEOUT = timeout

        # Set up a test grammar with some rules
        test1 = self.get_test_function()
        test2 = self.get_test_function()

        class TestRule(MappingRule):
            mapping = {
                "say <dictation>": Function(test1),
                "hello world": Function(test2),
            }
            extras = [Dictation("dictation")]

        grammar = Grammar("test")
        grammar.add_rule(TestRule())
        grammar.load()
        self.assertTrue(grammar.loaded)

        # Test that mapping 1 can be recognised fully
        self.assert_mimic_success("say", "hello")
        self.assert_test_function_called(test1, 1)

        # Start recognising mapping 1 again, then sleep for a bit
        self.assert_mimic_success("say")
        time.sleep(timeout)

        # The rest of mapping 1 should not match
        self.assert_mimic_failure("testing")
        self.assert_test_function_called(test1, 1)  # still only called 1 time

        # Should be able to match mapping 2 now
        self.assert_mimic_success("hello world")
        self.assert_test_function_called(test2, 1)

        # Test that it works with a break shorter than the timeout value
        self.assert_mimic_success("say")
        time.sleep(timeout / 2)
        self.assert_mimic_success("hello")
        self.assert_test_function_called(test1, 2)

        # Test with a timeout of 0 (no timeout)
        timeout = 0
        self.engine.config.NEXT_PART_TIMEOUT = timeout
        self.assert_mimic_success("say")
        time.sleep(0.1)  # sleep for 100ms
        self.assert_test_function_called(test1, 2)  # no change
        self.assert_mimic_success("testing")
        self.assert_test_function_called(test1, 3)

        # Test without a sleep between rule parts
        self.assert_mimic_success("say", "testing")
        self.assert_test_function_called(test1, 4)

        # Test that mapping 2 still has no issue matching
        self.assert_mimic_success("hello world")
        self.assert_test_function_called(test2, 2)

    def test_long_sequence_rule(self):
        """
        Test that the engine can recognise a long sequence rule and that the
        timeout functionality works correctly.
        """
        timeout = 0.1
        self.engine.config.NEXT_PART_TIMEOUT = timeout

        # Set up a test grammar with some rules
        test1 = self.get_test_function()
        test2 = self.get_test_function()

        class TestRule(MappingRule):
            mapping = {
                "testing": Function(test1),
                "testing <dictation> testing <dictation>": Function(test2),
            }
            extras = [Dictation("dictation")]

        grammar = Grammar("test")
        grammar.add_rule(TestRule())
        grammar.load()
        self.assertTrue(grammar.loaded)

        # Test that mapping 2 can be recognised fully
        self.assert_mimic_success("testing", "hello", "testing")
        self.assert_mimic_success("hello")
        self.assert_test_function_called(test2, 1)
        self.assert_test_function_called(test1, 0)

        # Start recognising mapping 2 again, then sleep for a bit
        self.assert_mimic_success("testing")
        time.sleep(timeout + 0.1)

        # Only mapping 1 should have been processed
        self.assert_test_function_called(test1, 1)
        self.assert_test_function_called(test2, 1)

        # Test that it works with a break shorter than the timeout value
        self.assert_mimic_success("testing")
        time.sleep(timeout / 2)
        self.assert_mimic_success("hello")
        time.sleep(timeout / 2)
        self.assert_mimic_success("testing")
        time.sleep(timeout / 2)
        self.assert_mimic_success("hello")
        self.assert_test_function_called(test2, 2)

        # Test with a timeout of 0 (no timeout)
        timeout = 0
        self.engine.config.NEXT_PART_TIMEOUT = timeout
        self.assert_mimic_success("testing")
        time.sleep(0.1)  # sleep for 100ms
        self.assert_test_function_called(test2, 2)  # no changes

        # Test that mapping 1 won't process any more, even after a time.
        self.assert_test_function_called(test1, 1)

        # Mimicking the rest of the rule parts should make the rule process.
        self.assert_mimic_success("hello", "testing", "hello")
        self.assert_test_function_called(test2, 3)

    def test_engine_mimic(self):
        """The engine.mimic method matches any rule/mapping in one call."""
        # Note: it is normal for action.exec errors to be logged for this test.
        # Set up a test grammar with some rules
        test1 = self.get_test_function()
        test2 = self.get_test_function()
        test3 = self.get_test_function()
        test4 = self.get_test_function()

        class TestRule(MappingRule):
            mapping = {
                "testing": Function(test1),
                "testing <dictation> testing": Function(test2),
                "test with multiple words": Function(test3),
                "forward [<n>]": Function(test4)
            }
            extras = [
                Dictation("dictation"),
                IntegerRef("n", 1, 3)
            ]

        grammar = Grammar("test")
        grammar.add_rule(TestRule())
        grammar.load()

        def exec_mimic_action(words):
            # Pass each word to Mimic
            Mimic(*words.split(" ")).execute()

        # Test with the engine's mimic method and the Mimic action
        for f in [self.engine.mimic, exec_mimic_action]:
            self.reset_test_functions()

            # Test mapping 1
            f("testing")
            # engine.mimic will not match speech in sequence like
            # engine.mimic_phrases
            self.assert_test_function_called(test1, 1)
            self.assert_test_function_called(test2, 0)
            self.assert_test_function_called(test3, 0)

            # Test that partial matches of mapping 2 fail.
            if f is exec_mimic_action:
                # ActionBase.execute() catches and logs raised errors, so don't use
                # assertRaises for Mimic(...).execute()
                f("testing testing")
                f("testing hello")
            else:
                # engine.mimic(..) will raise MimicFailure
                self.assertRaises(MimicFailure, f, "testing testing")
                self.assertRaises(MimicFailure, f, "testing hello")

            # Neither test function should have been called
            self.assert_test_function_called(test1, 1)
            self.assert_test_function_called(test2, 0)
            self.assert_test_function_called(test3, 0)

            # Test that full matches of mapping 2 are successful
            f("testing hello testing")
            self.assert_test_function_called(test1, 1)
            self.assert_test_function_called(test2, 1)
            self.assert_test_function_called(test3, 0)

            # Test mapping 3
            f("test with multiple words")
            self.assert_test_function_called(test1, 1)
            self.assert_test_function_called(test2, 1)
            self.assert_test_function_called(test3, 1)  # mapping 3 processed
            self.assert_test_function_called(test4, 0)

            # Test mapping 4
            f("forward")
            self.assert_test_function_called(test4, 1)
            f("forward one")
            self.assert_test_function_called(test4, 2)


# ---------------------------------------------------------------------


if __name__ == '__main__':
    unittest.main()
