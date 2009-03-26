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


from ..base.integer_base import (MapIntBuilder, CollectionIntBuilder,
                                 MagnitudeIntBuilder, IntegerBase)
from ..base.digits_base import DigitsBase


int_0           = MapIntBuilder({"zero": 0})
int_1_9         = MapIntBuilder({
                                 "one":    1,
                                 "two":    2,
                                 "three":  3,
                                 "four":   4,
                                 "five":   5,
                                 "six":    6,
                                 "seven":  7,
                                 "eight":  8,
                                 "nine":   9,
                               })
int_10_19       = MapIntBuilder(dict(zip(
                    "ten eleven twelve thirteen fourteen fifteen sixteen"
                    " seventeen eighteen nineteen".split(),
                    range(10, 20))))
int_20_90_10    = MapIntBuilder(dict(zip(
                    "twenty thirty forty fifty sixty seventy"
                    " eighty ninety".split(),
                    range(2, 10))))
int_20_99       = MagnitudeIntBuilder(
                    10, "<multiplier> [<remainder>]",
                    [int_20_90_10], [int_1_9])
int_and_1_99    = CollectionIntBuilder("[and] <element>",
                    [int_1_9, int_10_19, int_20_99])
int_100s        = MagnitudeIntBuilder(100,
                    "[<multiplier>] hundred [<remainder>]",
                    [int_1_9], [int_and_1_99])
int_100big      = MagnitudeIntBuilder(100,
                    "[<multiplier>] hundred [<remainder>]",
                    [int_10_19, int_20_99], [int_and_1_99])
int_1000s       = MagnitudeIntBuilder(1000,
                    "[<multiplier>] thousand [<remainder>]",
                    [int_1_9, int_10_19, int_20_99, int_100s],
                    [int_and_1_99, int_100s])
int_1000000s    = MagnitudeIntBuilder(1000000,
                    "[<multiplier>] million [<remainder>]",
                    [int_1_9, int_10_19, int_20_99, int_100s, int_1000s],
                    [int_and_1_99, int_100s, int_1000s])

class Integer(IntegerBase):
    _builders = [int_0, int_1_9, int_10_19, int_20_99,
                 int_100s, int_100big, int_1000s, int_1000000s]

class Digits(DigitsBase):
    _digits = [("zero", "oh"), "one", "two", "three", "four",
               "five", "six", "seven", "eight", "nine"]
