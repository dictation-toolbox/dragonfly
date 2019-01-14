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

from dragonfly import CompoundRule, MimicFailure
from dragonfly.test import (RuleTestCase, TestContext, RuleTestGrammar)


# ==========================================================================

class TestRules(RuleTestCase):
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
        self.assertRaises(MimicFailure, self.engine.mimic, "test context")

        # Test again after going back into context.
        context.active = True
        results = self.recognize_node("test context").words()
        assert results == ["test", "context"]

    def test_grammar_context(self):
        """ Verify that the engine works correctly with grammar
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
        """ Verify that the engine supports exclusive grammars. """
        # This is here as grammar exclusivity is context related.
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

# ==========================================================================

if __name__ == "__main__":
    unittest.main()
