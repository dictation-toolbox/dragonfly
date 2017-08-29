import unittest

from dragonfly import CompoundRule
from jsgf.dragonfly2jsgf import *


class TranslatorCase(unittest.TestCase):
    translator = Translator()


class PlainCase(TranslatorCase):
    def test_plain(self):
        spec = "Hello world"
        expected = "public <test> = hello world;"
        rule = self.translator.translate_to_rule("test", spec, True)
        self.assertEqual(expected, rule.compile())

    def test_plain_match(self):
        spec = "Hello world"
        rule = self.translator.translate_to_rule("test", spec, True)
        self.assertTrue(rule.matches("hello world"))


class BadRuleCase(TranslatorCase):
    def test_undefined_rule(self):
        spec = "Hello <person>"
        self.assertRaises(Exception, Compound, spec)

    def test_bad_dragonfly_spec(self):
        def is_bad(spec):
            self.assertRaises(ParserError, self.translator.translate, spec)

        is_bad("Hello world[")
        is_bad("Hello world(")
        is_bad("Hello world)")
        is_bad("Hello world#")
        is_bad("Hello world<")
        is_bad("<[a]>")
        is_bad("<a>>")
        is_bad("[]")


class OptionalCase(TranslatorCase):
    def test_simple_optional(self):
        spec = "Hello [glorious] world"
        expected = "public <test> = hello [glorious] world;"
        self.assertEqual(expected,
                         self.translator.translate_to_rule("test", spec, True)
                         .compile())

    def test_complex_optional(self):
        spec = "[[hello] world] hi"
        expected = "public <test> = [[hello] world] hi;"

        self.assertEqual(expected,
                         self.translator.translate_to_rule("test", spec, True)
                         .compile())


class ChoiceCase(TranslatorCase):
    """
    Test case for testing whether dragonfly choices compile correctly into
    JSGF
    """
    def test_with_choice(self):
        spec = "Hello <person>"
        compound_rule = CompoundRule(name="greet", spec=spec, extras=[
            Choice("person", {"Bob": "Bob", "John": "John"})
        ])
        expected = "public <greet> = hello (bob|john);"
        rule = self.translator.translate_rule(compound_rule)
        self.assertEqual(expected, rule.compile())

    def test_choice_match(self):
        spec = "Hello <person>"
        compound_rule = CompoundRule(name="greet", spec=spec, extras=[
            Choice("person", {"Bob": "Bob", "John": "John"})
        ])
        rule = self.translator.translate_rule(compound_rule)
        self.assertTrue(rule.matches("hello Bob"))
        self.assertTrue(rule.matches("HELLO BOB"))


class GrammarCase(TranslatorCase):
    def test_simple_rule_grammar(self):
        grammar = Grammar("test")
        rule = CompoundRule(name="test", spec="hello world")
        grammar.add_rule(rule)
        jsgf_grammar = self.translator.translate_grammar(grammar)
        self.assertTrue(jsgf_grammar.rules[0].matches("HELLO WORLD"))


if __name__ == '__main__':
    unittest.main()
