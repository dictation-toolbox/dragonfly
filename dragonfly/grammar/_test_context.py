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
from dragonfly import Context, AppContext


class TestContextOperations(unittest.TestCase):

    def setUp(self):
        self.context_yes = Context()
        self.context_no = AppContext("never")

    def test_logic(self):
        self._check_match(self.context_yes,   True)
        self._check_match(self.context_no,    False)
        self._check_match(~self.context_yes,  False)
        self._check_match(~self.context_no,   True)
        self._check_match(self.context_yes & self.context_yes,   True)
        self._check_match(self.context_yes & self.context_no,    False)
        self._check_match(self.context_no  & self.context_yes,   False)
        self._check_match(self.context_no  & self.context_no,    False)
        self._check_match(self.context_yes | self.context_yes,   True)
        self._check_match(self.context_yes | self.context_no,    True)
        self._check_match(self.context_no  | self.context_yes,   True)
        self._check_match(self.context_no  | self.context_no,    False)
        self._check_match(self.context_yes & ~self.context_no,   True)
        self._check_match(self.context_yes & ~self.context_yes,  False)

    def _check_match(self, context, expected, executable="", title="",
                     handle=None):
        self.assertEqual(context.matches(executable, title, handle),
                         expected)


if __name__ == '__main__':
    unittest.main()
