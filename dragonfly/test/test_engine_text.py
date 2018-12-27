# -*- encoding: utf-8 -*-
#
# This file is part of Dragonfly.
# (c) Copyright 2018 by Dane Finlay
# Licensed under the LGPL.
#
#   Dragonfly is free software: you can redistribute it and/or modify it 
#   under the terms of the GNU Lesser General Public License as published 
#   by the Free Software Foundation, either version 3 of the License, or 
#   (at your option) any later version.
#
#   Dragonfly is distributed in the hope that it will be useful, but 
#   WITHOUT ANY WARRANTY; without even the implied warranty of 
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU 
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public 
#   License along with Dragonfly.  If not, see 
#   <http://www.gnu.org/licenses/>.
#

import unittest

from dragonfly.engines import EngineBase
from dragonfly import (Literal, Dictation, Sequence, Repetition,
                       CompoundRule, MimicFailure, get_engine, List,
                       DictList, ListRef, DictListRef, RecognitionHistory,
                       Rule)
from dragonfly.engines.backend_text.dictation import TextDictationContainer
from dragonfly.test import (ElementTester, RecognitionFailure, RuleTestCase,
                            TestContext, RuleTestGrammar)


# --------------------------------------------------------------------------

class TestEngineText(unittest.TestCase):

    def setUp(self):
        engine = get_engine("text")
        assert isinstance(engine, EngineBase)
        assert engine.name == "text"
        engine.connect()
        self.engine = engine

    def tearDown(self):
        self.engine.disconnect()

    def test_literal(self):
        """ Verify that the text engine is usable. """
        tester = ElementTester(Literal("hello world"))
        results = tester.recognize("hello world")
        assert results == "hello world"

        # Check that recognition failure is possible.
        results = tester.recognize("goodbye")
        assert results is RecognitionFailure

    def test_dictation(self):
        """ Verify that the text engine can mimic dictation. """
        tester = ElementTester(Dictation("text"))
        results = tester.recognize("HELLO WORLD")
        assert isinstance(results, TextDictationContainer)
        assert results.format() == "hello world"

        # Check that an empty string results in recognition failure.
        results = tester.recognize("")
        assert results is RecognitionFailure

    def test_mixed_dictation(self):
        """ Verify that the text engine can mimic rules with Dictation and
            Literal elements. """
        seq = Sequence([Literal("hello"), Dictation("text")])
        tester = ElementTester(seq)
        results = tester.recognize("hello WORLD")
        assert results[0] == "hello"
        assert isinstance(results[1], TextDictationContainer)
        assert results[1].format() == "world"

        # Check that strings not starting with "hello" result in recognition
        # failure.
        results = tester.recognize("goodbye world")
        assert results is RecognitionFailure

    def test_unicode_literals(self):
        """ Verify that the text engine can mimic literals using non-ascii
            characters. """
        tester = ElementTester(Literal(u"Привет, как дела?"))
        results = tester.recognize(u"Привет, как дела?")
        assert results == u"Привет, как дела?"

        # Check that recognition failure is possible.
        results = tester.recognize(u"Привет")
        assert results is RecognitionFailure
        results = tester.recognize(u"до свидания")
        assert results is RecognitionFailure

    def test_repetition(self):
        """ Verify that the text engine can mimic a rule using a Repetition
            element. """
        rep = Repetition(Sequence([Literal("hello"), Dictation("text")]),
                         min=1, max=16)
        tester = ElementTester(rep)

        # Test with one repetition.
        results = tester.recognize("hello WORLD")
        assert len(results) == 1
        assert results[0][0] == "hello"
        assert isinstance(results[0][1], TextDictationContainer)
        assert results[0][1].format() == "world"

        # Test with two repetitions.
        results = tester.recognize("hello WORLD hello TESTING")
        assert len(results) == 2
        assert results[0][0] == "hello"
        assert isinstance(results[0][1], TextDictationContainer)
        assert results[0][1].format() == "world"
        assert results[1][0] == "hello"
        assert isinstance(results[1][1], TextDictationContainer)
        assert results[1][1].format() == "testing"

        # Check that incomplete repetitions result in recognition
        # failure.
        results = tester.recognize("hello")
        assert results is RecognitionFailure
        results = tester.recognize("hello world")
        assert results is RecognitionFailure
        results = tester.recognize("hello WORLD hello")
        assert results is RecognitionFailure


class TestRules(RuleTestCase):
    def test_multiple_rules(self):
        """ Verify that the text engine successfully mimics each rule in a
            grammar with multiple rules. """
        self.add_rule(CompoundRule(name="r1", spec="hello"))
        self.add_rule(CompoundRule(name="r2", spec="see you"))
        assert self.recognize_node("hello").words() == ["hello"]
        assert self.recognize_node("see you").words() == ["see", "you"]

    def test_list(self):
        """ Verify that the text engine can mimic a rule using a ListRef
            element. """
        lst = List("fruit")
        lst.append("apple")
        self.grammar.add_list(lst)
        self.add_rule(Rule("fav_fruit", ListRef("fruit_ref", lst),
                           exported=True))

        # Test that the list item "apple" can be recognized.
        assert self.recognize_node("apple").words() == ["apple"]

        # Update the list and try again.
        lst.append("banana")

        # If recognition fails, then the list wasn't updated correctly.
        assert self.recognize_node("banana").words() == ["banana"]

    def test_dict_list(self):
        """ Verify that the text engine can mimic a rule using a DictListRef
            element. """
        lst = DictList("fruit")
        lst["mango"] = False
        self.grammar.add_list(lst)
        self.add_rule(Rule("fav_fruit", DictListRef("fruit_ref", lst),
                           exported=True))

        # Test that the list item "mango" can be recognized.
        assert self.recognize_node("mango").words() == ["mango"]

        # Update the list and try again.
        lst["mandarin"] = True

        # If recognition fails, then the list wasn't updated correctly.
        assert self.recognize_node("mandarin").words() == ["mandarin"]

    def test_rule_context(self):
        """ Verify that the text engine works correctly with rule
            contexts."""
        context = TestContext(True)
        self.add_rule(CompoundRule(name="r1", spec="test context",
                                   context=context))

        # Test that the rule matches when in-context.
        results = self.recognize_node("test context").words()
        assert results == ["test", "context"]

        # Go out of context and test again.
        # Use the engine's mimic method because recognize_node won't return
        # RecognitionFailure like ElementTester.recognize does.
        context.active = False
        self.assertRaises(MimicFailure, self.engine.mimic, "test context")

        # Test again after going back into context.
        context.active = True
        results = self.recognize_node("test context").words()
        assert results == ["test", "context"]

    def test_grammar_context(self):
        """ Verify that the text engine works correctly with grammar
            contexts."""
        # Recreate the RuleTestGrammar using a context and add a rule.
        context = TestContext(True)
        self.grammar = RuleTestGrammar(context=context)
        self.add_rule(CompoundRule(name="r1", spec="test context"))

        # Test that the rule matches when in-context.
        results = self.recognize_node("test context").words()
        assert results == ["test", "context"]

        # Go out of context and test again.
        context.active = False
        self.assertRaises(MimicFailure, self.engine.mimic, "test context")

        # Test again after going back into context.
        context.active = True
        results = self.recognize_node("test context").words()
        assert results == ["test", "context"]

    def test_exclusive_grammars(self):
        """ Verify that the text engine supports exclusive grammars. """
        # Set up two grammars to test with.
        grammar1 = self.grammar
        grammar1.add_rule(CompoundRule(spec="grammar one"))
        grammar2 = RuleTestGrammar(name="Grammar2")
        grammar2.add_rule(CompoundRule(spec="grammar two"))
        grammar1.load()
        grammar2.load()

        # Set grammar1 as exclusive and make some assertions.
        grammar1.set_exclusiveness(True)
        results = grammar1.recognize_node("grammar one").words()
        assert results == ["grammar", "one"]
        self.assertRaises(MimicFailure, self.engine.mimic, "grammar two")

        # Set grammar1 as no longer exclusive and make some assertions.
        grammar1.set_exclusiveness(False)
        results = grammar1.recognize_node("grammar one").words()
        assert results == ["grammar", "one"]
        results = grammar2.recognize_node("grammar two").words()
        assert results == ["grammar", "two"]

    def test_recognition_observers(self):
        """ Verify that the text engine notifies recognition observers
            correctly. """
        class TestRecognitionHistory(RecognitionHistory):
            def __init__(self, length=10):
                super(TestRecognitionHistory, self).__init__(length)
                self.begins = 0
                self.failures = 0

            def on_begin(self):
                super(TestRecognitionHistory, self).on_begin()
                self.begins += 1

            def on_failure(self):
                self.failures += 1

        history = TestRecognitionHistory()
        history.register()
        self.add_rule(CompoundRule(name="r1", spec="hello"))
        self.add_rule(CompoundRule(name="r2", spec="see you"))

        # Mimic twice and check that history received the words.
        assert self.recognize_node("hello").words() == ["hello"]
        assert self.recognize_node("see you").words() == ["see", "you"]
        assert history == [["hello"], ["see", "you"]]

        # Check that on_begin() was called twice.
        assert history.begins == 2

        # Check that on_begin() and on_failure() get called for failed
        # recognitions.
        self.assertRaises(MimicFailure, self.engine.mimic, "test failure")
        assert history.begins == 3
        assert history.failures == 1
