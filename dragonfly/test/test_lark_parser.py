# coding=utf-8

import unittest
import string

from dragonfly.parsing.parse import spec_parser, CompoundTransformer
from dragonfly import Compound, Literal, Sequence, Optional, Empty, Alternative

# ===========================================================================

extras = {"an_extra": Alternative([Literal(u"1"), Literal(u"2")])}


def check_parse_tree(spec, expected):
    tree = spec_parser.parse(spec)
    output = CompoundTransformer(extras).transform(tree)
    assert output.element_tree_string() == expected.element_tree_string()
    return output


class TestLarkParser(unittest.TestCase):
    def test_literal(self):
        check_parse_tree("test   ", Literal(u"test"))

    def test_multiple_literals(self):
        check_parse_tree("test  hello world ", Literal(u"test hello world"))

    def test_parens(self):
        check_parse_tree("(test )   ", Literal(u"test"))

    def test_punctuation(self):
        check_parse_tree(",", Literal(u","))
        check_parse_tree("test's   ", Literal(u"test's"))
        check_parse_tree("cul-de-sac   ", Literal(u"cul-de-sac"))

    def test_sequence(self):
        check_parse_tree(
            " test <an_extra> [op]",
            Sequence([Literal(u"test"), extras["an_extra"], Optional(Literal(u"op"))]),
        )

    def test_alternative_no_parens(self):
        check_parse_tree(
            " test |[op] <an_extra>",
            Alternative(
                [
                    Literal(u"test"),
                    Sequence([Optional(Literal(u"op")), extras["an_extra"]]),
                ]
            ),
        )

    def test_alternative_parens(self):
        check_parse_tree(
            "( test |[op] <an_extra>)",
            Alternative(
                [
                    Literal(u"test"),
                    Sequence([Optional(Literal(u"op")), extras["an_extra"]]),
                ]
            ),
        )

    def test_optional_alternative(self):
        check_parse_tree("[test|test's]", Optional(Alternative([Literal(u"test"), Literal(u"test's")])))

    def test_digit_in_word(self):
        check_parse_tree("F2", Literal(u"F2"))

    def test_unicode(self):
        check_parse_tree(u"touché", Literal(u"touché"))

    def test_bool_special_in_sequence(self):
        output = check_parse_tree(
            " test <an_extra> [op] {test_special}",
            Sequence([Literal(u"test"), extras["an_extra"], Optional(Literal(u"op"))]),
        )
        assert output.test_special == True
        assert all(getattr(child, 'test_special', None) == None for child in output.children)

    def test_other_special_in_sequence(self):
        output = check_parse_tree(
            " test <an_extra> [op] {test_special=4}",
            Sequence([Literal(u"test"), extras["an_extra"], Optional(Literal(u"op"))]),
        )
        assert output.test_special == 4
        assert all(getattr(child, 'test_special', None) == None for child in output.children)

    def test_bool_special_in_alternative(self):
        output = check_parse_tree(
            "foo | bar {test_special} | baz",
            Alternative([
                Literal(u"foo"),
                Literal(u"bar"),
                Literal(u"baz"),
            ]),
        )
        assert getattr(output.children[0], 'test_special', None) == None
        assert output.children[1].test_special == True
        assert getattr(output.children[2], 'test_special', None) == None

    def test_other_special_in_alternative(self):
        output = check_parse_tree(
            "foo | bar {test_special=4} | baz",
            Alternative([
                Literal(u"foo"),
                Literal(u"bar"),
                Literal(u"baz"),
            ]),
        )
        assert getattr(output.children[0], 'test_special', None) == None
        assert output.children[1].test_special == 4
        assert getattr(output.children[2], 'test_special', None) == None


# ===========================================================================

if __name__ == "__main__":
    unittest.main()
