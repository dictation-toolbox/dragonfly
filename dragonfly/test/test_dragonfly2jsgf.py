import unittest

import jsgf.ext

from dragonfly.engines.backend_sphinx.dragonfly2jsgf import *
from dragonfly import *
from dragonfly.parser import ParserError
from dragonfly import List as DragonflyList, DictList as DragonflyDictList


# Some JSGF class aliases for readability
JRule, JSeq, JOpt = jsgf.Rule, jsgf.Sequence, jsgf.OptionalGrouping
JAlt, JRef, JRep, = jsgf.AlternativeSet, jsgf.RuleRef, PatchedRepeat
JDict = jsgf.ext.Dictation


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


class RepetitionCase(TranslatorCase):
    def test_repetition_with_no_max(self):
        r = Rule("test", Repetition(Literal("hello")), exported=True)
        expected = LinkedRule("test", True, JRep("hello"), r)
        actual = self.translator.translate_rule(r).jsgf_rule
        self.assertEqual(actual, expected)

    def test_repetition_with_max(self):
        """Repetition limits are ignored for all rules"""
        r = Rule("test", Repetition(Literal("hello"), max=3), exported=True)
        expected_expansion = JRep("hello")
        expected = LinkedRule("test", True, expected_expansion, r)
        actual = self.translator.translate_rule(r).jsgf_rule
        self.assertEqual(actual, expected)

        # Test again with a higher max value
        r = Rule("test", Repetition(Literal("hello"), max=6), exported=True)
        expected_expansion = JRep("hello")
        expected = LinkedRule("test", True, expected_expansion, r)
        actual = self.translator.translate_rule(r).jsgf_rule
        self.assertEqual(actual, expected)

    def test_with_dictation(self):
        """
        Test that rules involving dictation translate the same regardless of the
        min/max values of the Repetition element.
        """
        r = Rule("test", Repetition(Dictation()), exported=True)
        expected = LinkedRule("test", True, JRep(JDict()), r)
        self.assertEqual(self.translator.translate_rule(r).jsgf_rule, expected)

        r = Rule("test", Repetition(Dictation(), 1, 16), exported=True)
        self.assertEqual(self.translator.translate_rule(r).jsgf_rule, expected)


class ListsCase(TranslatorCase):
    def setUp(self):
        self.fruit_list = DragonflyList("fruit")
        self.fruit_list.append("apple")
        self.fruit_list_ref = ListRef("fruit_ref", self.fruit_list)

        self.dict_list = DragonflyDictList("fruit_dict")
        self.dict_list["apple"] = "yep"
        self.dict_list["mango"] = "nope"
        self.dict_list_ref = DictListRef("fruit_dict_ref", self.dict_list)

    def test_list(self):
        actual = self.translator.translate_list(self.fruit_list)
        expected = JRule("fruit", False, JAlt("apple"))
        self.assertEqual(expected, actual)

    def test_list_ref(self):
        element = self.fruit_list_ref
        state = self.translator.translate_list_ref(TranslationState(element))
        jsgf_rule = JRule("fruit", False, JAlt(*self.fruit_list))
        self.assertEqual(JRef(jsgf_rule), state.expansion)
        self.assertListEqual([jsgf_rule], state.dependencies)

    def test_list_referencing_rule(self):
        element = self.fruit_list_ref
        r = Rule("fav_fruit", element, exported=True)
        state = self.translator.translate_rule(r)
        list_rule = JRule("fruit", False, JAlt(*self.fruit_list))
        expected_rule = LinkedRule("fav_fruit", True, JRef(list_rule), r)
        self.assertEqual(state.jsgf_rule, expected_rule)

    def test_dict_list(self):
        actual = self.translator.translate_dict_list(self.dict_list)
        expected = JRule("fruit_dict", False, JAlt("apple", "mango"))
        self.assertEqual(expected, actual)

    def test_dict_list_ref(self):
        element = self.dict_list_ref
        state = self.translator.translate_dict_list_ref(TranslationState(element))
        expected_rule = JRule("fruit_dict", False, JAlt("apple", "mango"))
        self.assertEqual(JRef(expected_rule), state.expansion)
        self.assertListEqual([expected_rule], state.dependencies)

    def test_dict_list_referencing_rule(self):
        element = self.dict_list_ref
        r = Rule("fruits", element, exported=True)
        state = self.translator.translate_rule(r)
        list_rule = JRule("fruit_dict", False, JAlt("apple", "mango"))
        expected_rule = LinkedRule("fruits", True, JRef(list_rule), r)
        self.assertEqual(state.jsgf_rule, expected_rule)


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
        rule = self.translator.translate_rule(compound_rule).jsgf_rule
        self.assertEqual(expected, rule.compile())

    def test_choice_match(self):
        spec = "Hello <person>"
        compound_rule = CompoundRule(name="greet", spec=spec, extras=[
            Choice("person", {"Bob": "Bob", "John": "John"})
        ])
        rule = self.translator.translate_rule(compound_rule).jsgf_rule
        self.assertTrue(rule.matches("hello Bob"))


class MappingRuleCase(TranslatorCase):
    def test_int_ref(self):
        r1 = MappingRule(
            name="test",
            mapping={
                "back <n>": Key("backspace:%(n)d"),
                "kill [<n>]": Key("delete:%(n)d"),
            },
            extras=[
                IntegerRef("n", 1, 5)
            ],
            defaults={
                "n": 1
            }
        )

        state = self.translator.translate_rule(r1)
        numbers = ["one", "two", "three", "four"]
        n = JRule("n", False, JAlt(*numbers))
        self.assertListEqual(state.dependencies, [n])
        self.assertEqual(
            state.jsgf_rule,
            JRule("test", True, JAlt(
                JSeq("back", JRef(n)),
                JSeq("kill", JOpt(JRef(n))))))

        # Test that matching works correctly
        self.assertTrue(state.jsgf_rule.matches("kill"))
        for s in numbers:
            self.assertTrue(state.dependencies[0].matches(s))
            self.assertTrue(state.jsgf_rule.matches("back %s" % s),
                            "'back %s' did not match" % s)
            self.assertTrue(state.jsgf_rule.matches("kill %s" % s),
                            "'kill %s' did not match" % s)


class GrammarCase(TranslatorCase):
    def test_simple_rule_grammar(self):
        grammar = Grammar("test")
        rule = CompoundRule(name="test", spec="hello world")
        grammar.add_rule(rule)
        jsgf_grammar = self.translator.translate_grammar(grammar)
        self.assertTrue(jsgf_grammar.rules[0].matches("HELLO WORLD"))

    def test_using_rule_ref(self):
        rule1 = Rule("rule", Literal("hello"), exported=True)
        rule_ref = RuleRef(rule1, name="rule_ref")
        state = TranslationState(rule_ref)
        self.translator.translate_rule_ref(state)
        self.assertEqual(state.element, rule_ref)
        expected_rule = JRule("rule_ref", True, "hello")
        self.assertListEqual(state.dependencies, [expected_rule])
        self.assertEqual(state.expansion, JRef(expected_rule))

    def test_repeated_referenced_dictation(self):
        """
        Test that dragonfly rules containing Dictation referenced by a RuleRef with
        a Repetition element as an ancestor is translated correctly, with rules
        joined as necessary.
        """
        g = Grammar("test")

        # Add two simple rules, a more complex MappingRule and a rule referencing it
        # that allows repetition of its mappings
        r1 = Rule("dict", Dictation("dictation"))
        r2 = Rule("test1", Repetition(RuleRef(r1)), exported=True)
        r3 = MappingRule("mapping", mapping={
            "testing": ActionBase(),
            "hello <dictation>": ActionBase(),
            "<dictation>": ActionBase(),
        }, extras=[Dictation("dictation")])
        r4 = Rule("test2", Repetition(RuleRef(r3)), exported=True)
        g.add_rule(r2)
        g.add_rule(r4)

        # Translate the 'test' grammar and make some assertions
        translated = self.translator.translate_grammar(g)
        expected_test1 = LinkedRule("test1", True, JRep(JDict()), r1)

        # Note: this is not how the engine sees MappingRules with Dictation
        # elements: they are further processed later on into JSGF SequenceRules.
        # This is the format the rules should be in for the later processing.

        expected_test2 = LinkedRule("test2", True, JRep(
            JAlt("testing", JSeq("hello", JDict()), JDict())
        ), r4)

        # Neither of the referenced rules should be in the final grammar, only the
        # two joined rules
        self.assertListEqual(translated.rules, [expected_test1, expected_test2])


if __name__ == '__main__':
    unittest.main()
