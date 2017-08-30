import unittest
from jsgf import *


class BasicGrammarCase(unittest.TestCase):
    def setUp(self):
        rule2 = HiddenRule("greetWord", AlternativeSet("hello", "hi"))
        rule3 = HiddenRule("name", AlternativeSet("peter", "john", "mary",
                                                  "anna"))
        rule1 = PublicRule("greet", RequiredGrouping(RuleRef(rule2),
                                                     RuleRef(rule3)))
        self.grammar = Grammar("test")
        self.grammar.add_rules(rule1, rule2, rule3)
        self.rule1 = rule1
        self.rule2 = rule2
        self.rule3 = rule3

    def test_basic_grammar_compile(self):
        expected = "#JSGF V1.0 UTF-8 en;\n" \
                   "grammar test;\n" \
                   "public <greet> = (<greetWord><name>);\n" \
                   "<greetWord> = (hello|hi);\n" \
                   "<name> = (peter|john|mary|anna);\n"

        compiled = self.grammar.compile_grammar(charset_name="UTF-8",
                                                language_name="en",
                                                jsgf_version="1.0")
        self.assertEqual(expected, compiled)

    def test_remove_dependent_rule(self):
        self.assertRaises(GrammarError, self.grammar.remove_rule, "greetWord")
        self.assertRaises(GrammarError, self.grammar.remove_rule, "name")

        self.grammar.remove_rule("greet")
        self.assertListEqual([self.rule2, self.rule3], self.grammar.rules)


class SpeechMatchCase(unittest.TestCase):
    def assert_matches(self, speech, rule):
        self.assertTrue(rule.matches(speech))

    def assert_no_match(self, speech, rule):
        self.assertFalse(rule.matches(speech))

    def test_single_rule_match(self):
        grammar = Grammar("test")
        rule = HiddenRule("greet", Sequence(
            AlternativeSet("hello", "hi"), "world"
        ))
        grammar.add_rules(rule)
        self.assert_matches("hello world", rule)
        self.assert_matches("hello world".swapcase(), rule)
        self.assert_matches("hi world", rule)
        self.assert_no_match("hey world", rule)
        self.assert_no_match("hello", rule)
        self.assert_no_match("world", rule)
        self.assert_no_match("", rule)

    def test_multi_rule_match(self):
        grammar = Grammar("test")
        rule2 = HiddenRule("greetWord", AlternativeSet("hello", "hi"))
        rule3 = HiddenRule("name", AlternativeSet("peter", "john",
                                                  "mary", "anna"))
        rule1 = PublicRule("greet",
                           RequiredGrouping(
                               RuleRef(rule2),
                               RuleRef(rule3))
                           )
        grammar.add_rules(rule1, rule2, rule3)

        # Rule 1
        self.assert_matches("hello john", rule1)
        self.assert_matches("hello john".swapcase(), rule1)
        self.assert_no_match("hello", rule1)
        self.assert_no_match("john", rule1)
        self.assert_no_match("", rule1)

        # Rule 2
        self.assert_matches("hello", rule2)
        self.assert_matches("HELLO", rule2)
        self.assert_matches("hi", rule2)
        self.assert_matches("HI", rule2)
        self.assert_no_match("", rule2)

        # Rule 3
        self.assert_matches("john", rule3)
        self.assert_no_match("", rule3)


class VisibleRulesCase(unittest.TestCase):
    """
    Test the 'visible_rules' property of the Grammar class.
    """
    def setUp(self):
        grammar1 = Grammar("test")
        self.rule1 = HiddenRule("rule1", "Hello")
        self.rule2 = HiddenRule("rule2", "Hey")
        self.rule3 = HiddenRule("rule3", "Hi")
        grammar1.add_rules(self.rule1, self.rule2, self.rule3)
        self.grammar1 = grammar1

        grammar2 = Grammar("test2")
        self.rule4 = PublicRule("rule4", "Hello")
        self.rule5 = PublicRule("rule5", "Hey")
        self.rule6 = HiddenRule("rule6", "Hi")
        grammar2.add_rules(self.rule4, self.rule5, self.rule6)
        self.grammar2 = grammar2

    def test_none(self):
        self.assertListEqual(self.grammar1.visible_rules, [])

    def test_many(self):
        self.assertListEqual(self.grammar2.visible_rules, [self.rule4, self.rule5])


class RootGrammarCase(BasicGrammarCase):
    def setUp(self):
        super(RootGrammarCase, self).setUp()
        self.rule5 = HiddenRule("greetWord", AlternativeSet("hello", "hi"))
        self.rule4 = PublicRule("greet", Sequence(RuleRef(self.rule5), "there"))
        self.rule6 = PublicRule("partingPhrase", AlternativeSet("goodbye", "see you"))

    def test_compile(self):
        root = RootGrammar(rules=self.grammar.rules, name="root")

        expected = "#JSGF V1.0 UTF-8 en;\n" \
                   "grammar root;\n" \
                   "public <root> = (<greet>);\n" \
                   "<greet> = (<greetWord><name>);\n" \
                   "<greetWord> = (hello|hi);\n" \
                   "<name> = (peter|john|mary|anna);\n"

        self.assertEqual(root.compile_grammar(charset_name="UTF-8", language_name="en",
                                              jsgf_version="1.0"), expected)

    def test_compile_add_remove_rule(self):
        root = RootGrammar(rules=[self.rule5, self.rule4], name="root")

        expected = "#JSGF V1.0 UTF-8 en;\n" \
                   "grammar root;\n" \
                   "public <root> = (<greet>);\n" \
                   "<greetWord> = (hello|hi);\n" \
                   "<greet> = <greetWord> there;\n"

        self.assertEqual(root.compile_grammar(charset_name="UTF-8",
                                              language_name="en",
                                              jsgf_version="1.0"), expected)

        root.add_rule(self.rule6)
        expected = "#JSGF V1.0 UTF-8 en;\n" \
                   "grammar root;\n" \
                   "public <root> = (<greet>|<partingPhrase>);\n" \
                   "<greetWord> = (hello|hi);\n" \
                   "<greet> = <greetWord> there;\n" \
                   "<partingPhrase> = (goodbye|see you);\n"

        self.assertEqual(root.compile_grammar(charset_name="UTF-8",
                                              language_name="en",
                                              jsgf_version="1.0"), expected)

        # Test removing the partingPhrase rule
        root.remove_rule("partingPhrase")
        expected = "#JSGF V1.0 UTF-8 en;\n" \
                   "grammar root;\n" \
                   "public <root> = (<greet>);\n" \
                   "<greetWord> = (hello|hi);\n" \
                   "<greet> = <greetWord> there;\n"

        self.assertEqual(root.compile_grammar(charset_name="UTF-8",
                                              language_name="en",
                                              jsgf_version="1.0"), expected)

    def test_match(self):
        # Only rule1 should match
        root = RootGrammar(rules=self.grammar.rules, name="root")
        self.assertListEqual(root.find_matching_rules("Hello John"), [self.rule1])
        self.assertListEqual(root.find_matching_rules("HELLO mary"), [self.rule1])
        self.assertListEqual(root.find_matching_rules("hello ANNA"), [self.rule1])

    def test_match_add_remove(self):
        root = RootGrammar(rules=[self.rule5, self.rule4], name="root")
        self.assertListEqual(root.find_matching_rules("Hello there"), [self.rule4])
        self.assertListEqual(root.find_matching_rules("Hi there"), [self.rule4])

        # Add a rule
        root.add_rule(self.rule6)
        self.assertListEqual(root.find_matching_rules("Goodbye"), [self.rule6])
        self.assertListEqual(root.find_matching_rules("See you"), [self.rule6])

        # Remove it and test again
        root.remove_rule("partingPhrase")
        self.assertListEqual(root.find_matching_rules("Goodbye"), [])
        self.assertListEqual(root.find_matching_rules("See you"), [])

    def test_remove_last_visible_rule(self):
        root = RootGrammar(rules=[self.rule5, self.rule4], name="root")
        self.assertRaises(GrammarError, root.remove_rule, "greet")


if __name__ == '__main__':
    unittest.main()
