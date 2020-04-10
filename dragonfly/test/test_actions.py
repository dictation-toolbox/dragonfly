# -*- encoding: windows-1252 -*-
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

from dragonfly.actions.action_base import Repeat
from dragonfly.actions.action_function import Function
from dragonfly.actions.action_key import Key
from dragonfly.actions.action_mimic import Mimic
from dragonfly.actions.action_paste import Paste
from dragonfly.actions.action_text import Text


#===========================================================================

class TestNonAsciiText(unittest.TestCase):

    def test_non_ascii_text(self):
        """ Test handling of non-ASCII characters in Text action. """

        action = Text(u"touché")
        self.assertEqual(str(action), "%r" % (u"touché",))


class TestNonAsciiKey(unittest.TestCase):

    def test_non_ascii_key(self):
        """ Test handling of non-ASCII characters in Key action. """

        action = Key(u"é")
        self.assertEqual(str(action), "[%r]" % (u"é",))


class TestNonAsciiActionSeries(unittest.TestCase):

    def test_non_ascii_key(self):
        """ Test handling of non-ASCII characters in ActionSeries actions.
        """

        action = Key(u"é") + Text(u"á")
        self.assertEqual(str(action), "[%r]+%r" % (u"é", u"á"))

        action = Key(u"é") | Text(u"á")
        self.assertEqual(str(action), "[%r]|%r" % (u"é", u"á"))


class TestNonAsciiFunction(unittest.TestCase):

    def test_non_ascii_function(self):
        """ Test handling of non-ASCII characters in Function action. """

        action = Function(lambda: u"é")
        expected = u"\\xe9" if PY2 else u"é"
        self.assertIn(expected, str(action))


class TestNonAsciiPaste(unittest.TestCase):

    def test_non_ascii_paste(self):
        """ Test handling of non-ASCII characters in Paste action. """

        action = Paste("touché")
        self.assertEqual(str(action), "Paste(%r)" % ("touché",))


class TestNonAsciiMimic(unittest.TestCase):

    def test_non_ascii_mimic(self):
        """ Test handling of non-ASCII characters in Mimic action. """

        action = Mimic("touché")
        self.assertEqual(str(action), "Mimic(%r)" % ("touché",))


class TestRepeat(unittest.TestCase):

    def test_repeat(self):
        """ Test handling of Repeat elements """

        r1 = Repeat("n")
        self.assertEqual(r1.factor({"n": 3}), 3)
        r2 = Repeat("n", 3)
        self.assertEqual(r2.factor({"n": 3}), 6)
        r3 = Repeat(3)
        self.assertEqual(r3.factor(), 3)
        r4 = Repeat(3, "n")
        self.assertEqual(r4.factor({"n": 3}), 6)


#===========================================================================

if __name__ == "__main__":
    unittest.main()
