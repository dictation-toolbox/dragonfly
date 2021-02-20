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
        # Test a range of non-compound integer words.
        ("null",                                                        0),
        ("eins",                                                        1),
        ("ein",                                                         1),
        ("zwei",                                                        2),
        ("drei",                                                        3),
        ("vier",                                                        4),
        ("fuenf",                                                       5),
        ("sechs",                                                       6),
        ("sieben",                                                      7),
        ("acht",                                                        8),
        ("neun",                                                        9),
        ("zehn",                                                       10),
        ("elf",                                                        11),
        ("zwoelf",                                                     12),
        ("dreizehn",                                                   13),
        ("vierzehn",                                                   14),
        ("fuenfzehn",                                                  15),
        ("sechzehn",                                                   16),
        ("siebzehn",                                                   17),
        ("achtzehn",                                                   18),
        ("neunzehn",                                                   19),
        ("zwanzig",                                                    20),
        ("ein und zwanzig",                                            21),
        ("zwei und zwanzig",                                           22),
        ("drei und zwanzig",                                           23),
        ("ein und dreissig",                                           31),
        ("vier und dreissig",                                          34),
        ("fuenf und vierzig",                                          45),
        ("sechs und fuenfzig",                                         56),
        ("sieben und sechzig",                                         67),
        ("acht und siebzig",                                           78),
        ("neun und achtzig",                                           89),
        ("hundert",                                                   100),
        ("ein hundert",                                               100),
        ("ein hundert eins",                                          101),
        ("ein hundert ein",                            RecognitionFailure),
        ("ein hundert drei und zwanzig",                              123),
        ("drei hundert neun und achtzig",                             389),
        ("ein tausend eins",                                         1001),
        ("ein tausend ein",                            RecognitionFailure),
        ("ein tausend ein hundert ein und dreissig",                 1131),
        ("ein und dreissig tausend ein hundert ein und dreissig",   31131),
        ("ein hundert ein und dreissig tausend ein hundert ein "
         "und dreissig",                                           131131),
        ("million",                                               1000000),
        ("millionen",                                  RecognitionFailure),
        ("eine million eins",                                     1000001),
        ("eine million ein",                           RecognitionFailure),
        ("eine million zwei tausend eins",                        1002001),
        ("eine million zwei tausend ein",              RecognitionFailure),
        ("eine million ein hundert ein und dreissig tausend ein "
         "hundert ein und dreissig",                              1131131),
        ("zwei millionen",                                        2000000),
        ("ein hundert eins millionen",                          101000000),
        ("ein hundert ein millionen",                  RecognitionFailure),

        # Test a range of compound integer words.
        ("einundzwanzig",                                              21),
        ("zweiundzwanzig",                                             22),
        ("dreiundzwanzig",                                             23),
        ("einunddreissig",                                             31),
        ("vierunddreissig",                                            34),
        ("fuenfundvierzig",                                            45),
        ("sechsundfuenfzig",                                           56),
        ("siebenundsechzig",                                           67),
        ("achtundsiebzig",                                             78),
        ("neunundachtzig",                                             89),
        ("ein hundert dreiundzwanzig",                                123),
        ("ein hundert einunddreissig",                                131),
        ("drei hundert neunundachtzig",                               389),
        ("ein tausend ein hundert einunddreissig",                   1131),
        ("einunddreissig tausend ein hundert einunddreissig",       31131),
        ("ein hundert einunddreissig tausend ein hundert "
         "einunddreissig",                                         131131),
        ("eine million ein hundert einunddreissig tausend ein "
         "hundert einunddreissig",                                1131131),
    ]
