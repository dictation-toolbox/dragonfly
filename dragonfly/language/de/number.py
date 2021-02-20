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
German language implementations of Integer and Digits classes
============================================================================

"""

from ..base.integer_internal  import (MapIntBuilder, CollectionIntBuilder,
                                      MagnitudeIntBuilder, IntegerContentBase)
from ..base.digits_internal   import DigitsContentBase


#---------------------------------------------------------------------------

int_0           = MapIntBuilder({
                                 "null":         0,
                               })
int_1_9_eins    = MapIntBuilder({
                                 "eins":         1,
                                 "zwei":         2,
                                 "drei":         3,
                                 "vier":         4,
                                 "fuenf":        5,
                                 "sechs":        6,
                                 "sieben":       7,
                                 "acht":         8,
                                 "neun":         9,
                               })
int_1_9         = MapIntBuilder({
                                 "ein":          1,
                                 "zwei":         2,
                                 "drei":         3,
                                 "vier":         4,
                                 "fuenf":        5,
                                 "sechs":        6,
                                 "sieben":       7,
                                 "acht":         8,
                                 "neun":         9,
                               })
int_1_eine      = MapIntBuilder({
                                 "eine":         1,
                               })
int_2_9         = MapIntBuilder({
                                 "zwei":         2,
                                 "drei":         3,
                                 "vier":         4,
                                 "fuenf":        5,
                                 "sechs":        6,
                                 "sieben":       7,
                                 "acht":         8,
                                 "neun":         9,
                               })
int_10_19       = MapIntBuilder({
                                 "zehn":        10,
                                 "elf":         11,
                                 "zwoelf":      12,
                                 "dreizehn":    13,
                                 "vierzehn":    14,
                                 "fuenfzehn":   15,
                                 "sechzehn":    16,
                                 "siebzehn":    17,
                                 "achtzehn":    18,
                                 "neunzehn":    19,
                               })
int_20_90_10    = MapIntBuilder({
                                 "zwanzig":      2,
                                 "dreissig":     3,
                                 "vierzig":      4,
                                 "fuenfzig":     5,
                                 "sechzig":      6,
                                 "siebzig":      7,
                                 "achtzig":      8,
                                 "neunzig":      9,
                               })


#---------------------------------------------------------------------------

def int_20_99_func(text):
    # Join any 'und' conjugates with the words on either side.
    return text.replace(" und", "und").replace("und ", "und")


#---------------------------------------------------------------------------

int_20_99       = MagnitudeIntBuilder(
                   factor      = 10,
                   spec        = "[<remainder> und] <multiplier>",
                   multipliers = [int_20_90_10],
                   remainders  = [int_1_9],
                   modifier_function = int_20_99_func,
                   modifier_mode = 1,  # MODE_AUGMENT (default)
                  )
int_and_1_99    = CollectionIntBuilder(
                   spec        = "<element>",
                   set         = [int_1_9_eins, int_10_19, int_20_99],
                  )
int_100s        = MagnitudeIntBuilder(
                   factor      = 100,
                   spec        = "[<multiplier>] hundert [<remainder>]",
                   multipliers = [int_1_9],
                   remainders  = [int_and_1_99],
                  )
int_100big      = MagnitudeIntBuilder(
                   factor      = 100,
                   spec        = "[<multiplier>] hundert [<remainder>]",
                   multipliers = [int_10_19, int_20_99],
                   remainders  = [int_and_1_99]
                  )
int_1000s       = MagnitudeIntBuilder(
                   factor      = 1000,
                   spec        = "[<multiplier>] tausend [<remainder>]",
                   multipliers = [int_1_9, int_10_19, int_20_99, int_100s],
                   remainders  = [int_and_1_99, int_100s]
                  )
int_1000000     = MagnitudeIntBuilder(
                   factor      = 1000000,
                   spec        = "[<multiplier>] million [<remainder>]",
                   multipliers = [int_1_eine],
                   remainders  = [int_and_1_99, int_100s, int_1000s],
                  )
int_1000000s    = MagnitudeIntBuilder(
                   factor      = 1000000,
                   spec        = "<multiplier> millionen [<remainder>]",
                   multipliers = [int_2_9, int_10_19, int_20_99, int_100s,
                                  int_1000s],
                   remainders  = [int_and_1_99, int_100s, int_1000s],
                  )


#---------------------------------------------------------------------------

class IntegerContent(IntegerContentBase):
    builders = [int_0, int_1_9, int_1_9_eins, int_10_19, int_20_99,
                int_100s, int_100big, int_1000s, int_1000000, int_1000000s]

class DigitsContent(DigitsContentBase):
    digits = [("null"), "eins", "zwei", "drei", "vier",
              "fuenf", "sechs", "sieben", "acht", "neun"]
