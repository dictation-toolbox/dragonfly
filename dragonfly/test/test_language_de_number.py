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
Test suite for German language Integer and Digits classes
============================================================================

"""

from dragonfly.test.infrastructure      import RecognitionFailure
from dragonfly.test.element_testcase    import ElementTestCase
from dragonfly.language.base.integer    import Integer
from dragonfly.language.de.number       import IntegerContent


#---------------------------------------------------------------------------

class GermanIntegerTestCase(ElementTestCase):
    """ Verify various German integers between 0 and 10**12. """
    def _build_element(self):
        return Integer(content=IntegerContent, min=0, max=10**12 - 1)
    input_output = [
                    ("null",                             0),
                    ("eins",                             1),
                    ("zwei",                             2),
                    ("drei",                             3),
                    ("vier",                             4),
                    ("fuenf",                            5),
                    ("sechs",                            6),
                    ("sieben",                           7),
                    ("acht",                             8),
                    ("neun",                             9),
                    ("zehn",                            10),
                    ("elf",                             11),
                    ("zwoelf",                          12),
                    ("dreizehn",                        13),
                    ("vierzehn",                        14),
                    ("fuenfzehn",                       15),
                    ("sechzehn",                        16),
                    ("siebzehn",                        17),
                    ("achtzehn",                        18),
                    ("neunzehn",                        19),
                    ("zwanzig",                         20),
                    ("ein und zwanzig",                 21),
                    ("zwei und zwanzig",                22),
                    ("drei und zwanzig",                23),
                    ("vier und dreissig",               34),
                    ("fuenf und vierzig",               45),
                    ("sechs und fuenfzig",              56),
                    ("sieben und sechzig",              67),
                    ("acht und siebzig",                78),
                    ("neun und achtzig",                89),
                    ("hundert",                        100),
                    ("ein hundert",                    100),
                    ("ein hundert drei und zwanzig",   123),
                   ]
