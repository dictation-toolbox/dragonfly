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
import time
import string

from dragonfly import parser


#===========================================================================

class TestParsers(unittest.TestCase):

    def setUp(self):
        pass

    def test_character_series(self):
        """ Test CharacterSeries parser class. """

        self._test_multiple(
            parser.CharacterSeries(string.letters),
            [
                ("abc", ["abc"]),
            ],
            must_finish = False)

    def test_repetition(self):
        """ Test repetition parser class. """
        word = parser.CharacterSeries(string.letters)
        whitespace = parser.CharacterSeries(string.whitespace)
        p = parser.Repetition(parser.Alternative((word, whitespace)))
        input_output = (
            ("abc", ["abc"] ),
            ("abc abc", ["abc", " ", "abc"]),
            ("abc abc\t\t\n   cba", ["abc", " ", "abc", "\t\t\n   ", "cba"]),
            )
        self._test_single(p, input_output)

    def test_optional_greedy(self):
        """ Test greedy setting of optional parser class. """
        input = "abc"
        p = parser.Sequence([
            parser.Sequence([
                parser.String("a"),
                parser.Optional(parser.String("b"), greedy = False)
                ]),
            parser.Sequence([
                parser.Optional(parser.String("b")),
                parser.String("c")
                ]),
            ])
        expected_output_1 = [["a", None], ["b", "c"]]
        expected_output_2 = [["a", "b"], [None, "c"]]

        state = parser.State(input)
        print "Parser:", p
        print "State:", state
        generator = p.parse(state)
        generator.next()
        root = state.build_parse_tree()
        self.assertEqual(root.value(), expected_output_1)
        print "Output 1:", expected_output_1
    
        generator.next()
        root = state.build_parse_tree()
        self.assertEqual(root.value(), expected_output_2)
        print "Output 2:", expected_output_2

    def _test_single(self, parser_element, input_output):
        p = parser.Parser(parser_element)
        print "Parser:", parser_element
        for input, output in input_output:
            print "Input:", input
            result = p.parse(input)
            print "Expected: %r" % output
            print "Result: %r" % result
            self.assertEqual(result, output)

    def _test_multiple(self, parser_element, input_outputs, must_finish = True):
        p = parser.Parser(parser_element)
        print "Parser:", parser_element
        for input, outputs in input_outputs:
            print "Input:", input
            results = p.parse_multiple(input, must_finish)
            self.assertEqual(len(results), len(outputs))
            for index, result, output in zip(xrange(len(results)), results, outputs):
                if isinstance(result, list): result = tuple(result)
                if isinstance(output, list): output = tuple(output)
                print "Expected: %r" % output
                print "Result %d: %r" % (index, result)
                self.assertEqual(result, output)


#===========================================================================

if __name__ == "__main__":
    unittest.main()
