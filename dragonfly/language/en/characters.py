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

"""
Characters in text symbols for the English language.
============================================================================

"""

from ...grammar.elements   import Choice, RuleRef, Repetition
from ...grammar.rule_base  import Rule


#---------------------------------------------------------------------------
# Letter names.

letter_names = {
                "alpha":     "a",
                "bravo":     "b",
                "charlie":   "c",
                "delta":     "d",
                "echo":      "e",
                "foxtrot":   "f",
                "golf":      "g",
                "hotel":     "h",
                "india":     "i",
                "juliett":   "j",
                "kilo":      "k",
                "lima":      "l",
                "mike":      "m",
                "november":  "n",
                "oscar":     "o",
                "papa":      "p",
                "quebec":    "q",
                "romeo":     "r",
                "sierra":    "s",
                "tango":     "t",
                "uniform":   "u",
                "victor":    "v",
                "whiskey":   "w",
                "x-ray":     "x",
                "yankee":    "y",
                "zulu":      "z",
               }
uppercase_prefix = "(cap | shift)"

lowercase_letter_names = letter_names
uppercase_letter_names = dict((name, char.upper())
                              for (name, char) in letter_names.items())


#---------------------------------------------------------------------------
# Digit names.

digit_names = {
               "zero":    "0",
               "one":     "1",
               "two":     "2",
               "three":   "3",
               "four":    "4",
               "five":    "5",
               "six":     "6",
               "seven":   "7",
               "eight":   "8",
               "nine":    "9",
              }


#---------------------------------------------------------------------------
# Symbol names.

symbol_names = {
                "enter":                                  "\n",
                "tab":                                    "\t",
                "space":                                  " ",
                "exclamation [mark]":                     "!",
                "at [sign]":                              "@",
                "(hash | pound) [sign]":                  "#",
                "dollar [sign]":                          "$",
                "percent [sign]":                         "%",
                "caret":                                  "^",
                "(ampersand | and sign)":                 "&",
                "(asterisk | star)":                      "*",
                "(left | open) (paren | parenthesis)":    "(",
                "(right | close) (paren | parenthesis)":  ")",
                "(hyphen | minus [sign])":                "-",
                "underscore":                             "_",
                "(equal | equals) [sign]":                "=",
                "plus":                                   "+",
                "backtick":                               "`",
                "tilde":                                  "~",
                "(left | open) bracket":                  "[",
                "(right | close) bracket":                "]",
                "(left | open) brace":                    "{",
                "(right | close) brace":                  "}",
                "backslash":                              "\\",
                "[vertical] bar":                         "|",
                "colon":                                  ":",
                "(apostrophe | single quote)":            "'",
                "double quote":                           '"',
                "comma":                                  ",",
                "(dot | period | full stop)":             ".",
                "slash":                                  "/",
                "left angle bracket":                     "<",
                "right angle bracket":                    ">",
                "question [mark]":                        "?",
               }


#---------------------------------------------------------------------------
# Aggregation of all char names.

char_names = dict(lowercase_letter_names)
char_names.update(digit_names)
char_names.update(symbol_names)


#---------------------------------------------------------------------------
# Helper functions to create special element classes.

def choice_wrap_class(choices):
    class _ChoiceWrapClass(RuleRef):
        _choices = choices
        def __init__(self, name):
            choice_element = Choice(name=None, choices=self._choices)
            choice_rule = Rule(element=choice_element)
            RuleRef.__init__(self, name=name, rule=choice_rule)
    return _ChoiceWrapClass

def choice_series_wrap_class(choices):
    class _ChoiceWrapClass(RuleRef):
        _choices = choices
        def __init__(self, name, min=1, max=8):
            choice_element   = Choice(name=None, choices=self._choices)
            choice_rule      = Rule(element=choice_element)
            choice_ref       = RuleRef(rule=choice_rule)
            series_element   = Repetition(child=choice_ref, min=min, max=max)
            series_rule      = Rule(element=series_element)
            RuleRef.__init__(self, name=name, rule=series_rule)
        def value(self, node):
            child_values = RuleRef.value(self, node)
            return "".join(child_values)
    return _ChoiceWrapClass


#---------------------------------------------------------------------------
# High-level, easy-to-use element classes.

LetterChoice  = choice_wrap_class(lowercase_letter_names)
LetterSeries  = choice_series_wrap_class(lowercase_letter_names)
CharChoice    = choice_wrap_class(char_names)
CharSeries    = choice_series_wrap_class(char_names)
