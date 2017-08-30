import unittest
from jsgf import *


class BasicGrammarCase(unittest.TestCase):
    def test_basic_grammar_compile(self):
        grammar = Grammar("test")
        rule2 = HiddenRule("greetWord", AlternativeSet("hello", "hi"))
        rule3 = HiddenRule("name", AlternativeSet("peter", "john", "mary",
                                                  "anna"))
        rule1 = PublicRule("greet", RequiredGrouping(
            RuleRef(rule2), RuleRef(rule3)))
        grammar.add_rules(rule1, rule2, rule3)

        expected = "#JSGF V1.0 UTF-8 en;\n" \
                   "grammar test;\n" \
                   "public <greet> = (<greetWord><name>);\n" \
                   "<greetWord> = (hello|hi);\n" \
                   "<name> = (peter|john|mary|anna);\n"

        self.assertEqual(grammar.compile_grammar(charset_name="UTF-8",
                                                 language_name="en",
                                                 jsgf_version="1.0"), expected)


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
    def test_none(self):
        grammar1 = Grammar("test")
        rule1 = HiddenRule("rule1", "Hello")
        rule2 = HiddenRule("rule2", "Hey")
        rule3 = HiddenRule("rule3", "Hi")
        grammar1.add_rules(rule1, rule2, rule3)
        self.assertListEqual(grammar1.visible_rules, [])

    def test_many(self):
        grammar1 = Grammar("test")
        rule1 = PublicRule("rule1", "Hello")
        rule2 = PublicRule("rule2", "Hey")
        rule3 = HiddenRule("rule3", "Hi")
        grammar1.add_rules(rule1, rule2, rule3)
        self.assertListEqual(grammar1.visible_rules, [rule1, rule2])


if __name__ == '__main__':
    unittest.main()
