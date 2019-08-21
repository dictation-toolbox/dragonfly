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
Dutch language implementations of Integer and Digits classes
============================================================================

"""

from ..base.integer_internal  import (MapIntBuilder, CollectionIntBuilder,
                                      MagnitudeIntBuilder, IntegerContentBase)
from ..base.digits_internal   import DigitsContentBase


#---------------------------------------------------------------------------

int_0           = MapIntBuilder({
                                 "nul": 0
                               })
int_1_9         = MapIntBuilder({
                                 "1":      1,  # Use "1" instead of "een"
                                               #  because the latter has
                                               #  multiple pronunciations.
                                 "twee":   2,
                                 "drie":   3,
                                 "vier":   4,
                                 "vijf":   5,
                                 "zes":    6,
                                 "zeven":  7,
                                 "acht":   8,
                                 "negen":  9,
                               })
int_10_19       = MapIntBuilder({
                                 "tien":      10,
                                 "elf":       11,
                                 "twaalf":    12,
                                 "dertien":   13,
                                 "veertien":  14,
                                 "vijftien":  15,
                                 "zestien":   16,
                                 "zeventien": 17,
                                 "achtien":   18,
                                 "negentien": 19,
                               })
int_20_90_10    = MapIntBuilder({
                                 "twintig":   2,
                                 "dertig":    3,
                                 "veertig":   4,
                                 "vijftig":   5,
                                 "zestig":    6,
                                 "zeventig":  7,
                                 "tachtig":   8,
                                 "negentig":  9,
                               })
int_20_99       = MagnitudeIntBuilder(
                   factor      = 10,
                   spec        = "[<remainder> en] <multiplier>",
                   multipliers = [int_20_90_10],
                   remainders  = [int_1_9]
                  )
int_en_1_99     = CollectionIntBuilder(
                   spec        = "[en] <element>",
                   set         = [int_1_9, int_10_19, int_20_99]
                  )
int_100s        = MagnitudeIntBuilder(
                   factor      = 100,
                   spec        = "[<multiplier>] honderd [<remainder>]",
                   multipliers = [int_1_9],
                   remainders  = [int_en_1_99]
                  )
int_100big      = MagnitudeIntBuilder(
                   factor      = 100,
                   spec        = "[<multiplier>] honderd [<remainder>]",
                   multipliers = [int_10_19, int_20_99],
                   remainders  = [int_en_1_99]
                  )
int_1000s       = MagnitudeIntBuilder(
                   factor      = 1000,
                   spec        = "[<multiplier>] duizend [<remainder>]",
                   multipliers = [int_1_9, int_10_19, int_20_99, int_100s],
                   remainders  = [int_en_1_99, int_100s]
                  )
int_1000000s    = MagnitudeIntBuilder(
                   factor      = 1000000,
                   spec        = "[<multiplier>] millioen [<remainder>]",
                   multipliers = [int_1_9, int_10_19, int_20_99, int_100s, int_1000s],
                   remainders  = [int_en_1_99, int_100s, int_1000s]
                  )


#---------------------------------------------------------------------------

class IntegerContent(IntegerContentBase):
    builders = [int_0, int_1_9, int_10_19, int_20_99,
                int_100s, int_100big, int_1000s, int_1000000s]

class DigitsContent(DigitsContentBase):
    digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
