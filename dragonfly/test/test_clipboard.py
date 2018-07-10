# encoding=utf-8
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

from dragonfly.util import Clipboard


class TestClipboard(unittest.TestCase):
    """
    Tests for the multi-platform Clipboard class.
    """
    def setUp(self):
        # Clear the clipboard before each test.
        Clipboard.clear_clipboard()

    def tearDown(self):
        Clipboard.clear_clipboard()

    def test_system_text_methods(self):
        text = "testing testing"
        Clipboard.set_system_text(text)
        self.assertEqual(Clipboard.get_system_text(), text)

    def test_clear_clipboard(self):
        # Put something on the system clipboard.
        Clipboard.set_system_text("something")

        # Clear it.
        Clipboard.clear_clipboard()

        # Then test that it has been cleared.
        self.assertEqual(Clipboard.get_system_text(), "")

    def test_empty(self):
        # A new clipboard has no content for the unicode format.
        c = Clipboard()

        # Neither does a new clipboard have text.
        self.assertFalse(c.has_text())

    def test_from_system_argument(self):
        # Test the optional from_system argument of Clipboard.__init__
        text = "something"
        Clipboard.set_system_text(text)
        c = Clipboard(from_system=True)
        self.assertEqual(c.text, text)
        self.assertTrue(c.has_text())

    def test_copy_from_system(self):
        text = "testing"
        Clipboard.set_system_text(text)
        c = Clipboard()

        # Test the method with clear=False (default)
        c.copy_from_system(clear=False)
        self.assertEqual(c.text, text)
        self.assertEqual(Clipboard.get_system_text(), text)

        # Test again with clear=True
        c = Clipboard()
        c.copy_from_system(clear=True)
        self.assertEqual(c.text, text)
        self.assertEqual(Clipboard.get_system_text(), "")

    def test_copy_to_system(self):
        text = "testing"
        c = Clipboard(text=text)
        c.copy_to_system()
        self.assertEqual(Clipboard.get_system_text(), text)

    def test_set_text(self):
        c = Clipboard()
        text = "test"
        c.set_text(text)
        self.assertTrue(c.has_text())
        self.assertEqual(c.get_text(), text)
        self.assertEqual(c.text, text)

    def test_backwards_compatibility(self):
        # The multi-platform class should be backwards compatible with the
        # Windows-only Clipboard class, at least for the constructor.
        text = u"unicode text"
        c = Clipboard(contents={13: text})
        c.copy_to_system()
        self.assertEqual(Clipboard.get_system_text(), text)

        # Test with the CF_TEXT format (1)
        text = "text"
        c = Clipboard(contents={1: text})
        c.copy_to_system()
        self.assertEqual(Clipboard.get_system_text(), text)

    def test_non_ascii(self):
        text = u"""
        ૱ ꠸ ┯ ┰ ┱ ┲ ❗ ► ◄ Ă ă 0 1 2 3 4 5 6 7 8 9 Ǖ ǖ Ꞁ ¤ ­ Ð ¢ ℥ Ω ℧ K ℶ
        ℷ ℸ ⅇ ⅊ ⚌ ⚍ ⚎ ⚏ ⚭ ⚮ ⌀ ⏑ ⏒ ⏓ ⏔ ⏕ ⏖ ⏗ ⏘ ⏙ ⏠ ⏡ ⏦ ᶀ ᶁ ᶂ ᶃ ᶄ ᶆ ᶇ ᶈ
        ᶉ ᶊ ᶋ ᶌ ᶍ ᶎ ᶏ ᶐ ᶑ ᶒ ᶓ ᶔ ᶕ ᶖ ᶗ ᶘ ᶙ ᶚ ᶸ ᵯ ᵰ ᵴ ᵶ ᵹ ᵼ ᵽ ᵾ ᵿ
        """
        Clipboard.set_system_text(text)
        self.assertEqual(Clipboard.get_system_text(), text)


if __name__ == '__main__':
    unittest.main()
