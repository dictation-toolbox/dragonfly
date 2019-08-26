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
from six import PY2

from dragonfly.windows.window import Window


#===========================================================================

class TestWindow(unittest.TestCase):

    def setUp(self):
        pass

    def test_set_handle(self):
        """ Test access to Window.handle property. """

        # Verify that only integers and longs are accepted.
        Window(0)
        Window(int(1))
        if PY2:
            Window(long(2))
        self.assertRaises(TypeError, Window, [None])
        self.assertRaises(TypeError, Window, ["string"])
        self.assertRaises(TypeError, Window, [3.4])

#===========================================================================

if __name__ == "__main__":
    unittest.main()
