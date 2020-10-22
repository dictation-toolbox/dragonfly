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

from dragonfly import CompoundRule, MimicFailure, Grammar, get_engine
from dragonfly.test import (RuleTestCase, TestContext, RuleTestGrammar)


# ==========================================================================

class TestRules(RuleTestCase):

    def setUp(self):
        RuleTestCase.setUp(self)
        engine = get_engine()
        if engine.name == 'natlink':
            # Stop Dragon from dictating text for the duration of these
            # tests. This is required when testing for mimic failures.
            self.temp_grammar = Grammar("temp")
            self.temp_grammar.add_rule(CompoundRule(spec="exclusive rule"))
            self.temp_grammar.load()
            self.temp_grammar.set_exclusiveness(True)

    def tearDown(self):
        RuleTestCase.tearDown(self)
        engine = get_engine()
        if engine.name == 'natlink':
            self.temp_grammar.set_exclusiveness(False)
            self.temp_grammar.unload()

    def process_grammars_context(self):
        engine = get_engine()
        if engine.name.startswith("sapi5"):
            engine.process_grammars_context()

    def test_multiple_rules(self):
        """ Verify that the engine successfully mimics each rule in a
            grammar with multiple rules. """
        self.add_rule(CompoundRule(name="r1", spec="hello"))
        self.add_rule(CompoundRule(name="r2", spec="see you"))
        assert self.recognize_node("hello").words() == ["hello"]
        assert self.recognize_node("see you").words() == ["see", "you"]

    def test_rule_context(self):
        """ Verify that the engine works correctly with rule contexts. """
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
        self.process_grammars_context()
        try:
            self.grammar.load()
            self.grammar.set_exclusiveness(True)
            self.assertRaises(MimicFailure, self.engine.mimic, "test context")
        finally:
            self.grammar.set_exclusiveness(False)
            self.grammar.unload()

        # Test again after going back into context.
        context.active = True
        self.process_grammars_context()
        results = self.recognize_node("test context").words()
        assert results == ["test", "context"]

    def test_grammar_context(self):
        """ Verify that the engine works correctly with grammar
            contexts."""
        # Recreate the RuleTestGrammar using a context and add a rule.
        context = TestContext(True)
        self.grammar = RuleTestGrammar(context=context)
        self.add_rule(CompoundRule(name="r1", spec="test context"))
        self.grammar.load()

        # Test that the rule matches when in-context.
        results = self.recognize_node("test context").words()
        assert results == ["test", "context"]

        # Go out of context and test again.
        context.active = False
        self.process_grammars_context()
        try:
            self.grammar.set_exclusiveness(True)
            self.assertRaises(MimicFailure, self.engine.mimic, "test context")
        finally:
            self.grammar.set_exclusiveness(False)

        # Test again after going back into context.
        context.active = True
        self.process_grammars_context()
        results = self.recognize_node("test context").words()
        assert results == ["test", "context"]

    def test_exclusive_grammars(self):
        """ Verify that the engine supports exclusive grammars. """
        # This is here as grammar exclusivity is context related.
        # Set up two grammars to test with.
        class TestRule(CompoundRule):
            def __init__(self, spec):
                CompoundRule.__init__(self, spec=spec)
                self.words = None

            def _process_recognition(self, node, extras):
                self.words = self.spec

        grammar1 = Grammar(name="Grammar1")
        grammar1.add_rule(TestRule(spec="grammar one"))
        grammar2 = Grammar(name="Grammar2")
        grammar2.add_rule(TestRule(spec="grammar two"))
        grammar3 = Grammar(name="Grammar3")
        grammar3.add_rule(TestRule(spec="grammar three"))
        grammar1.load()
        grammar2.load()
        grammar3.load()

        # Set grammar1 as exclusive and make some assertions.
        grammar1.set_exclusiveness(True)
        self.engine.mimic("grammar one")
        assert grammar1.rules[0].words == "grammar one"
        self.assertRaises(MimicFailure, self.engine.mimic, "grammar two")

        # Set grammar2 as exclusive and make some assertions.
        # Both exclusive grammars should be active.
        grammar2.set_exclusiveness(True)
        self.engine.mimic("grammar one")
        assert grammar1.rules[0].words == "grammar one"
        self.engine.mimic("grammar two")
        assert grammar2.rules[0].words == "grammar two"

        # Non-exclusive grammar 'grammar3' should not be active.
        self.assertRaises(MimicFailure, self.engine.mimic, "grammar three")

        # Set both grammars as no longer exclusive and make some assertions.
        grammar1.set_exclusiveness(False)
        grammar2.set_exclusiveness(False)
        if get_engine().name == 'natlink':
            self.temp_grammar.set_exclusiveness(False)
        self.engine.mimic("grammar one")
        assert grammar1.rules[0].words == "grammar one"
        self.engine.mimic("grammar two")
        assert grammar2.rules[0].words == "grammar two"
        self.engine.mimic("grammar three")
        assert grammar3.rules[0].words == "grammar three"

# ==========================================================================

if __name__ == "__main__":
    unittest.main()
