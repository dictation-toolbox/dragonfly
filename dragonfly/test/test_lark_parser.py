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


# ===========================================================================

if __name__ == "__main__":
    unittest.main()
