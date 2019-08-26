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
Test suite for Dutch language Integer and Digits classes
============================================================================

"""

from dragonfly.test.infrastructure      import RecognitionFailure
from dragonfly.test.element_testcase    import ElementTestCase
from dragonfly.language.base.integer    import Integer
from dragonfly.language.nl.number       import IntegerContent


#---------------------------------------------------------------------------

class DutchIntegerTestCase(ElementTestCase):
    """ Verify various Dutch integers between 0 and 10**12. """
    def _build_element(self):
        return Integer(content=IntegerContent, min=0, max=10**12 - 1)
    input_output = [
                    ("nul",        0),
                    ("1",          1),
                    ("twee",       2),
                    ("drie",       3),
                    ("vier",       4),
                    ("vijf",       5),
                    ("zes",        6),
                    ("zeven",      7),
                    ("acht",       8),
                    ("negen",      9),
                    ("tien",      10),
                    ("elf",       11),
                    ("twee en twintig",                            22),
                    ("honderd drie en twintig",                   123),
                    ("honderd en vier en twintig",                124),
                    ("zeven honderd negen en tachtig",            789),
                    ("vier en dertig honderd zes en vijftig",    3456),
                   ]
