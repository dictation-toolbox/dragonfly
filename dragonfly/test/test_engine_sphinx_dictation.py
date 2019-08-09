import unittest

import time
import logging

from dragonfly import (CompoundRule, Function, Grammar, MappingRule)
from dragonfly.engines import (EngineBase, EngineError, MimicFailure,
                               get_engine)
from dragonfly.grammar.elements import Dictation, Literal, Sequence
from dragonfly.grammar.recobs import RecognitionObserver
from dragonfly.test import (ElementTester, RuleTestGrammar)
from dragonfly.test.test_engine_sphinx import SphinxEngineCase


# class DictationEngineTests(SphinxEngineCase):
class DictationEngineTests(object):
    """
    Tests for the engine's dictation functionality.

    Dictation andthese tests are temporarily **DISABLED** to make other
    changes easier.
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
