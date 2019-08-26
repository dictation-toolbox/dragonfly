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

"""
Arabic (ar) language implementations of Integer and Digits classes
============================================================================

"""

from ..base.integer_internal  import (MapIntBuilder, CollectionIntBuilder,
                                      MagnitudeIntBuilder, IntegerContentBase)
from ..base.digits_internal   import DigitsContentBase


#---------------------------------------------------------------------------

int_0           = MapIntBuilder({
                                 "صفر":         0,
                               })
int_1_9         = MapIntBuilder({
                                 "واحد":        1,
                                 "اثنان":       2,
                                 "ثلاثة":       3,
                                 "اربعة":       4,
                                 "خمسة":        5,
                                 "ستة":         6,
                                 "سبعة":        7,
                                 "ثمانية":      8,
                                 "تسعة":        9,
                               })
int_10_19       = MapIntBuilder({
                                 "عشرة":        10,
                                 "احدى عشر":    11,
                                 "اثنا عشر":    12,
                                 "ثلاثة عشر":   13,
                                 "اربعة عشر":   14,
                                 "خمسة عشر":    15,
                                 "ستة عشر":     16,
                                 "سبعة عشر":    17,
                                 "ثمانية عشر":  18,
                                 "تسعة عشر":    19,
                               })
int_20_90_10    = MapIntBuilder({
                                 "عشرون":        2,
                                 "ثلاثون":       3,
                                 "اربعون":       4,
                                 "خمسون":        5,
                                 "ستون":         6,
                                 "سبعون":        7,
                                 "ثمانون":       8,
                                 "تسعون":        9,
                               })
int_20_99       = MagnitudeIntBuilder(
                   factor      = 10,
                   spec        = "<multiplier> [<remainder>]",
                   multipliers = [int_20_90_10],
                   remainders  = [int_1_9],
                  )
int_and_1_99    = CollectionIntBuilder(
                   spec        = "[و] <element>",
                   set         = [int_1_9, int_10_19, int_20_99],
                  )
int_100s        = MagnitudeIntBuilder(
                   factor      = 100,
                   spec        = "[<multiplier>] hundred [<remainder>]",
                   multipliers = [int_1_9],
                   remainders  = [int_and_1_99],
                  )
int_100big      = MagnitudeIntBuilder(
                   factor      = 100,
                   spec        = "[<multiplier>] hundred [<remainder>]",
                   multipliers = [int_10_19, int_20_99],
                   remainders  = [int_and_1_99]
                  )
int_1000s       = MagnitudeIntBuilder(
                   factor      = 1000,
                   spec        = "[<multiplier>] thousand [<remainder>]",
                   multipliers = [int_1_9, int_10_19, int_20_99, int_100s],
                   remainders  = [int_and_1_99, int_100s]
                  )
int_1000000s    = MagnitudeIntBuilder(
                   factor      = 1000000,
                   spec        = "[<multiplier>] million [<remainder>]",
                   multipliers = [int_1_9, int_10_19, int_20_99, int_100s, int_1000s],
                   remainders  = [int_and_1_99, int_100s, int_1000s],
                  )


#---------------------------------------------------------------------------

class IntegerContent(IntegerContentBase):
    builders = [int_0, int_1_9, int_10_19, int_20_99,
                int_100s, int_100big, int_1000s, int_1000000s]

class DigitsContent(DigitsContentBase):
    digits = [("صفر", "اووه"), "واحد", "اثنان", "ثلاثة", "اربعة",
              "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
