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

import unittest
from dragonfly.engines import get_engine, EngineBase, EngineError


#---------------------------------------------------------------------------

class TestEngineNonexistent(unittest.TestCase):

    def test_get_engine_nonexistent(self):
        """ Verify that getting a nonexistent engine raises an error. """
        try:
            engine = get_engine("nonexistent")
        except EngineError:
            pass  # Expected exception, so ignore.
        else:
            assert False, ("Getting a nonexistent engine should have"
                           " raised an exception, but it didn't!")
