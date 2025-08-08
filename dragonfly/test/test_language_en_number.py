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
Test suite for English language Integer and Digits classes
============================================================================

"""

from dragonfly.test.infrastructure      import RecognitionFailure
from dragonfly.test.element_testcase    import ElementTestCase
from dragonfly.language.base.integer    import Integer
from dragonfly.language.base.digits     import Digits
from dragonfly.language.en.number       import IntegerContent
from dragonfly.language.en.number       import DigitsContent
from dragonfly.language.en.short_number import ShortIntegerContent


#---------------------------------------------------------------------------

class IntegerTestCase(ElementTestCase):
    """ Verify various integers between 0 and 10**12. """
    def _build_element(self):
        return Integer(content=IntegerContent, min=0, max=10**12 - 1)
    input_output = [
                    ("zero",       0),
                    ("oh",         0),
                    ("one",        1),
                    ("two",        2),
                    ("three",      3),
                    ("four",       4),
                    ("five",       5),
                    ("six",        6),
                    ("seven",      7),
                    ("eight",      8),
                    ("nine",       9),
                    ("ten",       10),
                    ("eleven",    11),
                    ("twelve",    12),
                    ("thirteen",  13),
                    ("fourteen",  14),
                    ("fifteen",   15),
                    ("sixteen",   16),
                    ("seventeen", 17),
                    ("eighteen",  18),
                    ("nineteen",  19),
                    ("seventy four hundred",    7400),
                    ("seventy four thousand",  74000),
                    ("two hundred and thirty four thousand five hundred sixty seven", 234567),
                   ]


class Limit3to13TestCase(ElementTestCase):
    """ Verify integer limits of range 3 -- 13. """
    def _build_element(self):
        return Integer(content=IntegerContent, min=3, max=13)
    input_output = [
                    ("oh",         RecognitionFailure),
                    ("zero",       RecognitionFailure),
                    ("one",        RecognitionFailure),
                    ("two",        RecognitionFailure),
                    ("three",      3),
                    ("four",       4),
                    ("five",       5),
                    ("six",        6),
                    ("seven",      7),
                    ("eight",      8),
                    ("nine",       9),
                    ("ten",       10),
                    ("eleven",    11),
                    ("twelve",    12),
                    ("thirteen",  13),
                    ("fourteen",   RecognitionFailure),
                    ("fifteen",    RecognitionFailure),
                    ("sixteen",    RecognitionFailure),
                    ("seventeen",  RecognitionFailure),
                    ("eighteen",   RecognitionFailure),
                    ("nineteen",   RecognitionFailure),
                   ]


class Limit23to46TestCase(ElementTestCase):
    """ Verify integer limits of range 23 -- 46. """
    def _build_element(self):
        return Integer(content=IntegerContent, min=23, max=46)
    input_output = [
                    ("twenty two",        RecognitionFailure),
                    ("twenty three",      23),
                    ("forty six",         46),
                    ("forty seven",       RecognitionFailure),
                   ]


class Limit230to349TestCase(ElementTestCase):
    """ Verify integer limits of range 230 -- 349. """
    def _build_element(self):
        return Integer(content=IntegerContent, min=230, max=349)
    input_output = [
                    ("two hundred twenty nine",     RecognitionFailure),
                    ("two hundred thirty",          230),
                    ("two hundred and thirty",      230),
                    ("two hundred and thirty zero", RecognitionFailure),
                    ("two hundred thirty one",      231),
                    ("two hundred and thirty one",  231),
                    ("three hundred forty nine",    349),
                    ("three hundred fifty zero",    RecognitionFailure),
                    ("three hundred fifty",         RecognitionFailure),
                   ]


class Limit350TestCase(ElementTestCase):
    """ Verify integer limits of range up to 350. """
    def _build_element(self):
        return Integer(content=IntegerContent, min=230, max=350)
    input_output = [
                    ("three hundred forty nine",    349),
                    ("three hundred fifty",         350),
                    ("three hundred fifty zero",    RecognitionFailure),
                    ("three hundred fifty one",     RecognitionFailure),
                   ]


class Limit351TestCase(ElementTestCase):
    """ Verify integer limits of range up to 351. """
    def _build_element(self):
        return Integer(content=IntegerContent, min=230, max=351)
    input_output = [
                    ("three hundred forty nine",    349),
                    ("three hundred fifty",         350),
                    ("three hundred fifty zero",    RecognitionFailure),
                    ("three hundred fifty one",     351),
                    ("three hundred fifty two",     RecognitionFailure),
                   ]


class DigitsTestCase(ElementTestCase):
    """ Verify that digits between 0 and 10 can be recognized. """
    def _build_element(self):
        return Digits(content=DigitsContent, min=1, max=5)
    input_output = [
                    ("zero",                                           [0]),
                    ("oh",                                             [0]),
                    ("one",                                            [1]),
                    ("two",                                            [2]),
                    ("three",                                          [3]),
                    ("four",                                           [4]),
                    ("five",                                           [5]),
                    ("six",                                            [6]),
                    ("seven",                                          [7]),
                    ("eight",                                          [8]),
                    ("nine",                                           [9]),
                    ("one zero",                                    [1, 0]),
                    ("ten",                             RecognitionFailure),
                    ("three four",                                  [3, 4]),
                    ("thirty five",                     RecognitionFailure),
                    ("one zero zero",                            [1, 0, 0]),
                    ("one hundred",                     RecognitionFailure),
                    ("three one four one five",            [3, 1, 4, 1, 5]),
                    ("nine two six five three",            [9, 2, 6, 5, 3]),
                    ("five eight nine seven",                 [5, 8, 9, 7]),
                    ("one two three four five six",     RecognitionFailure),
                   ]


class DigitsAsIntTestCase(ElementTestCase):
    """ Verify that Digits used with as_int=True gives correct values. """
    def _build_element(self):
        return Digits(content=DigitsContent, min=1, max=5, as_int=True)
    input_output = [
                    ("zero",                                             0),
                    ("oh",                                               0),
                    ("one",                                              1),
                    ("two",                                              2),
                    ("three",                                            3),
                    ("four",                                             4),
                    ("five",                                             5),
                    ("six",                                              6),
                    ("seven",                                            7),
                    ("eight",                                            8),
                    ("nine",                                             9),
                    ("one zero",                                        10),
                    ("ten",                             RecognitionFailure),
                    ("three four",                                      34),
                    ("thirty four",                     RecognitionFailure),
                    ("one zero zero",                                  100),
                    ("one hundred",                     RecognitionFailure),
                    ("three one four one five",                      31415),
                    ("nine two six five three",                      92653),
                    ("five eight nine seven",                         5897),
                    ("one two three four five six",     RecognitionFailure),
                   ]


class ShortIntegerTestCase(ElementTestCase):
    """ Verify line integer class working as expected """
    def _build_element(self):
        return Integer(content=ShortIntegerContent, min=0, max=10000000)
    input_output = [
                    ("one",                           1),
                    ("ten",                           10),
                    ("two two",                       22),
                    ("twenty three",                  23),
                    ("two three",                     23),
                    ("seventy",                       70),
                    ("seven zero",                    70),
                    ("hundred",                       100),
                    ("one oh three",                  103),
                    ("hundred three",                 103),
                    ("one twenty seven",              127),
                    ("one two seven",                 127),
                    ("one hundred twenty seven",      127),
                    ("two two two",                   222),
                    ("seven hundred",                 700),
                    ("thousand",                      1000),
                    ("seventeen hundred",             1700),
                    ("seventeen hundred fifty three", 1753),
                    ("seventeen fifty three",         1753),
                    ("one seven five three",          1753),
                    ("seventeen five three",          1753),
                    ("four thousand",                 4000),
                    ("ten thousand",                  10000),
                    ("ninety thousand",               90000),
                    ("four hundred thousand",         400000),
                    ("four hundred thousand and fifty", 400050),
                    ("four hundred thousand three hundred and forty two", 400342),
                    ("two hundred and thirty four thousand five hundred sixty seven", 234567),
                    ("five million two hundred and thirty four thousand five hundred sixty seven", 5234567),
                   ]
