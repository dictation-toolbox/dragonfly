# coding=utf-8
#
# This file is part of Dragonfly.
# (c) Copyright 2007, 2008 by Christo Butcher
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
import string

from dragonfly import parser
from dragonfly import Compound

#===========================================================================


class TestParsers(unittest.TestCase):

    def setUp(self):
        pass

    def test_character_series(self):
        """ Test CharacterSeries parser classes. """

        # Test with ascii characters
        self._test_multiple(
            parser.CharacterSeries(string.ascii_letters),
            [
                ("abc", ["abc"]),
            ],
            must_finish=False)

        # Test the Letters and Alphanumerics classes with a few inputs and
        # outputs
        input_outputs = [
            # Unicode strings
            (u"abc", [u"abc"]),
            # Mix of non-ascii characters
            (u"éèàâêùôöëäïüû", [u"éèàâêùôöëäïüû"]),
            (u"touché", [u"touché"]),
        ]
        self._test_multiple(
            parser.Letters(),
            input_outputs + [(string.digits, [])],
            must_finish=False
        )
        self._test_multiple(
            parser.Alphanumerics(),
            input_outputs + [(string.digits, [string.digits])],
            must_finish=False
        )

    def test_other_alphabets(self):
        """ Test that other alphabets also work. """
        # While the DNS and WSR engines are mostly limited to western
        # European languages (i.e. windows-1252), that doesn't necessarily
        # mean the parser needs to be.
        input_outputs = [
            (u"йцукенгшщзхъфывапролджэячсмитьбю",
             [u"йцукенгшщзхъфывапролджэячсмитьбю"]),
        ]
        self._test_multiple(
            parser.Letters(), input_outputs, must_finish=False
        )
        self._test_multiple(
            parser.Alphanumerics(), input_outputs, must_finish=False
        )

    def test_compound_element(self):
        """ Test the dragonfly Compound element. """
        # Compound is the element that the base dragonfly rule classes use.
        # It uses custom parser elements, so it needs to be tested separately.
        self.assertEqual(
            Compound(spec=u"touché").gstring(),
            u"(touché)"
        )
        self.assertEqual(
            Compound(spec=u"йцукенгшщзхъфывапролджэячсмитьбю").gstring(),
            u"(йцукенгшщзхъфывапролджэячсмитьбю)"
        )

    def test_repetition(self):
        """ Test repetition parser class. """
        word = parser.Letters()
        whitespace = parser.Whitespace()
        p = parser.Repetition(parser.Alternative((word, whitespace)))

        # Test with ascii letters
        input_output = (
            ("abc", ["abc"]),
            ("abc abc", ["abc", " ", "abc"]),
            ("abc abc\t\t\n   cba", ["abc", " ", "abc", "\t\t\n   ",
                                     "cba"]),
            )
        self._test_single(p, input_output)

        # Test with non-ascii letters
        input_output = (
            (u"êùö", [u"êùö"]),
            (u"êùö êùö", [u"êùö", u" ", u"êùö"]),
            (u"êùö êùö\t\t\n   öùê", [
                u"êùö", " ", u"êùö", u"\t\t\n   ", u"öùê"]),
        )
        self._test_single(p, input_output)

    def test_optional_greedy(self):
        """ Test greedy setting of optional parser class. """
        input = "abc"
        p = parser.Sequence([
            parser.Sequence([
                parser.String("a"),
                parser.Optional(parser.String("b"), greedy=False)
                ]),
            parser.Sequence([
                parser.Optional(parser.String("b")),
                parser.String("c")
                ]),
            ])
        expected_output_1 = [["a", None], ["b", "c"]]
        expected_output_2 = [["a", "b"], [None, "c"]]

        state = parser.State(input)
        generator = p.parse(state)
        next(generator)
        root = state.build_parse_tree()
        self.assertEqual(root.value(), expected_output_1)
        next(generator)
        root = state.build_parse_tree()
        self.assertEqual(root.value(), expected_output_2)

    def _test_single(self, parser_element, input_output):
        p = parser.Parser(parser_element)
        for input, output in input_output:
            result = p.parse(input)
            self.assertEqual(result, output)

    def _test_multiple(self, parser_element, input_outputs, must_finish=True):
        p = parser.Parser(parser_element)
        for input, outputs in input_outputs:
            results = p.parse_multiple(input, must_finish)
            self.assertEqual(len(results), len(outputs))
            for index, result, output in zip(list(range(len(results))), results, outputs):
                if isinstance(result, list): result = tuple(result)
                if isinstance(output, list): output = tuple(output)
                self.assertEqual(result, output)


#===========================================================================

if __name__ == "__main__":
    unittest.main()
