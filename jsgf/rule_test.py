import unittest

from jsgf import *


class RuleDependenciesCase(unittest.TestCase):
    """
    Test the 'dependencies' property of the Rule class.
    """
    def test_simple(self):
        rule2 = HiddenRule("greetWord", AlternativeSet("hello", "hi"))
        rule3 = HiddenRule("name", AlternativeSet("peter", "john", "mary", "anna"))
        rule1 = PublicRule("greet", RequiredGrouping(RuleRef(rule2), RuleRef(rule3)))
        self.assertSetEqual(rule1.dependencies, {rule2, rule3})

    def test_complex(self):
        rule2 = HiddenRule("greetWord", AlternativeSet("hello", "hi"))
        rule3 = HiddenRule("firstName", AlternativeSet("peter", "john", "mary", "anna"))
        rule4 = HiddenRule("lastName", AlternativeSet("smith", "ryan", "king", "turner"))
        rule5 = HiddenRule("name", RequiredGrouping(RuleRef(rule3),
                                                    OptionalGrouping(RuleRef(rule4))))
        rule1 = PublicRule("greet", RequiredGrouping(RuleRef(rule2), RuleRef(rule5)))
        self.assertSetEqual(rule1.dependencies, {rule2, rule3, rule4, rule5})


class RuleRefCount(unittest.TestCase):
    """
    Test the 'reference_count' property of the Rule class.
    """
    def setUp(self):
        self.rule = HiddenRule("greet", "hello")

    def test_simple(self):
        rule_refs = [RuleRef(self.rule)]
        self.assertEqual(1, self.rule.reference_count)
        rule_refs.pop()
        self.assertEqual(0, self.rule.reference_count)

    def test_with_grammar(self):
        grammar = Grammar()
        grammar.add_rule(self.rule)
        self.assertEqual(0, self.rule.reference_count, "rule '%s' is not independent.")
        grammar.add_rule(PublicRule("test", RuleRef(self.rule)))
        self.assertEqual(1, self.rule.reference_count, "rule '%s' is independent.")


if __name__ == '__main__':
    unittest.main()
