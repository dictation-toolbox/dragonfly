"""
Tests for the CMU Pocket Sphinx engine
"""

import unittest

import time

from sphinxwrapper import DefaultConfig

from dragonfly import *
from dragonfly import List as DragonflyList, DictList as DragonflyDict
from dragonfly.engines.backend_sphinx.engine import SphinxEngine


class SphinxEngineCase(unittest.TestCase):
    """
    Base TestCase class for Sphinx engine tests
    """
    def setUp(self):
        engine = get_engine("sphinx")
        assert isinstance(engine, SphinxEngine)
        assert engine.name == "sphinx"
        engine.connect()
        self.engine = engine

        # Save current config
        self.engine_config = self.engine.config

        # Set a default NEXT_PART_TIMEOUT value so there aren't weird timing errors
        # that break tests. Value of 0 means no timeout at all.
        self.engine.config.NEXT_PART_TIMEOUT = 0

        # Map for test functions
        self.test_map = {}

    def tearDown(self):
        # Restore saved config
        self.engine.config = self.engine_config
        self.engine.disconnect()
        self.test_map = {}

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
            self.engine.mimic(*phrases)
        except MimicFailure:
            self.fail("MimicFailure caught")

    def assert_mimic_failure(self, *phrases):
        self.assertRaises(MimicFailure, self.engine.mimic, *phrases)


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
            "NEXT_PART_TIMEOUT"
        ]

        class TestConfig(object):
            DECODER_CONFIG = DefaultConfig()
            LANGUAGE = "en"
            PYAUDIO_STREAM_KEYWORD_ARGS = {}
            NEXT_PART_TIMEOUT = 0

        def set_config(value):
            self.engine.config = value

        # Test with correct attributes
        self.assertIsNone(set_config(TestConfig()))

        # Delete each attribute and check that an AssertionError is raised upon
        # setting the config again
        for name in required:
            delattr(TestConfig, name)
            self.assertRaises(AssertionError, set_config, TestConfig())

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
        self.assert_mimic_success("testing")
        self.assert_test_function_called(test1, 3)

        # Test without a sleep between rule parts
        self.assert_mimic_success("say", "testing")
        self.assert_test_function_called(test1, 4)

        # Test that mapping 2 still has no issue matching
        self.assert_mimic_success("hello world")
        self.assert_test_function_called(test2, 2)


# ---------------------------------------------------------------------


if __name__ == '__main__':
    unittest.main()
