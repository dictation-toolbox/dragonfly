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
#   Use "1" instead of "een"
#   because the latter has
#   multiple pronunciations.

"""
Malaysian (ms) language implementations of Integer and Digits classes
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
                                 "satu":      1,
                                 "dua":       2,
                                 "tiga":      3,
                                 "empat":     4,
                                 "lima":      5,
                                 "enam":      6,
                                 "tujuh":     7,
                                 "lapan":     8,
                                 "sembilan":  9,
                               })
int_10_19       = MapIntBuilder({
                                 "sepuluh":       10,
                                 "sebelas":       11,
                                 "duabelas":      12,
                                 "tigabelas":     13,
                                 "empatbelas":    14,
                                 "limabelas":     15,
                                 "enambelas":     16,
                                 "tujuhbelas":    17,
                                 "lapanbelas":    18,
                                 "sembilanbelas": 19,
                               })
int_20_90_10    = MapIntBuilder({
                                 "duapuluh":       2,
                                 "tigapuluh":      3,
                                 "empatpuluh":     4,
                                 "limapuluh":      5,
                                 "enampuluh":      6,
                                 "tujuhpuluh":     7,
                                 "lapanpuluh":     8,
                                 "sembilanpuluh":  9,
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
                   spec        = "[<multiplier>] ratus [<remainder>]",
                   multipliers = [int_1_9],
                   remainders  = [int_en_1_99]
                  )
int_100big      = MagnitudeIntBuilder(
                   factor      = 100,
                   spec        = "[<multiplier>] ratus [<remainder>]",
                   multipliers = [int_10_19, int_20_99],
                   remainders  = [int_en_1_99]
                  )
int_1000s       = MagnitudeIntBuilder(
                   factor      = 1000,
                   spec        = "[<multiplier>] ribu [<remainder>]",
                   multipliers = [int_1_9, int_10_19, int_20_99, int_100s],
                   remainders  = [int_en_1_99, int_100s]
                  )
int_1000000s    = MagnitudeIntBuilder(
                   factor      = 1000000,
                   spec        = "[<multiplier>] juta [<remainder>]",
                   multipliers = [int_1_9, int_10_19, int_20_99, int_100s, int_1000s],
                   remainders  = [int_en_1_99, int_100s, int_1000s]
                  )


#---------------------------------------------------------------------------

class IntegerContent(IntegerContentBase):
    builders = [int_0, int_1_9, int_10_19, int_20_99,
                int_100s, int_100big, int_1000s, int_1000000s]

class DigitsContent(DigitsContentBase):
    digits = ["kosong","satu","dua","tiga","empat","lima",
	          "enam","tujuh","lapan","sembilan"]

