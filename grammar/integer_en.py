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
    This file implements Integer and Digits classes for the English language.
"""


import elements as elements_
from integer_base import LitNumBuilder, SetNumBuilder, \
                        MagnitudeNumBuilder, NumBase, DigitsBase


int_0           = LitNumBuilder(("zero", ), (0, ))
int_1_9         = LitNumBuilder(
                    "one two three four five six seven eight nine".split(),
                    range(1, 10))
int_10_19       = LitNumBuilder(
                    "ten eleven twelve thirteen fourteen fifteen sixteen"
                    " seventeen eighteen nineteen".split(),
                    range(10, 20))
int_20_90_10    = LitNumBuilder(
                    "twenty thirty forty fifty sixty seventy"
                    " eighty ninety".split(),
                    range(2, 10))
int_20_99       = MagnitudeNumBuilder(
                    None, 10, (int_20_90_10, ), (int_1_9, ),
                    optional_multiplier=False)
int_and_1_99    = SetNumBuilder(
                    (int_1_9, int_10_19, int_20_99),
                    prefix=elements_.Optional(elements_.Literal("and")))
int_100s        = MagnitudeNumBuilder(
                    elements_.Literal("hundred"), 100,
                    (int_1_9, ), (int_and_1_99, ))
int_1000s       = MagnitudeNumBuilder(
                    elements_.Literal("thousand"), 1000,
                    (int_1_9, int_10_19, int_20_99, int_100s),
                    (int_and_1_99, int_100s))

class Integer(NumBase):
    _element_builders = (int_0, int_1_9, int_10_19, int_20_99, int_100s, int_1000s)


class Digits(DigitsBase):
    _digits = (("zero", "oh"), "one", "two", "three", "four",
                "five", "six", "seven", "eight", "nine")
