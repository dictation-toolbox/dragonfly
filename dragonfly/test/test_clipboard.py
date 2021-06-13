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

import os
from tempfile import NamedTemporaryFile, mkdtemp
import unittest

from dragonfly import Clipboard


format_unicode = Clipboard.format_unicode
format_text = Clipboard.format_text
format_hdrop = Clipboard.format_hdrop


class TestClipboard(unittest.TestCase):
    """
    Tests for the Clipboard class.

    These should pass on all supported platforms.
    """

    #-----------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        # Save the current contents of the clipboard.
        cls.clipboard = Clipboard(from_system=True)

    @classmethod
    def tearDownClass(cls):
        # Restore the clipboard contents to what it was before the tests.
        cls.clipboard.copy_to_system()

    def setUp(self):
        # Clear the clipboard before each test.
        Clipboard.clear_clipboard()

    #-----------------------------------------------------------------------

    def test_get_set_system_text(self):
        # Test with an empty system clipboard.
        Clipboard.clear_clipboard()
        self.assertEqual(Clipboard.get_system_text(), u"")

        # Test setting a Unicode string on the system clipboard.
        text1 = u"Unicode text"
        Clipboard.set_system_text(text1)
        self.assertEqual(Clipboard.get_system_text(), text1)

        # Test setting a binary string on the system clipboard.
        # get_system_text() should return the equivalent Unicode string, as
        # format_unicode is preferred.
        Clipboard.set_system_text(b"text")
        self.assertEqual(Clipboard.get_system_text(), u"text")

        # Test that setting the text using None clears the clipboard.
        Clipboard.set_system_text(None)
        self.assertEqual(Clipboard.get_system_text(), u"")

    def test_clear_clipboard(self):
        # Put something on the system clipboard.
        Clipboard.set_system_text("something")

        # Clear it.
        Clipboard.clear_clipboard()

        # Then test that it has been cleared.
        self.assertEqual(Clipboard.get_system_text(), "")

    def test_convert_format_content(self):
        # Define a convenient shorthand function for testing the
        # Clipboard.convert_format_content() class method.
        def convert(format, content):  # pylint: disable=redefined-builtin
            return Clipboard.convert_format_content(format, content)

        # Text strings used with format_text (ANSI) are converted.
        self.assertEqual(convert(format_text, u"text"), b"text")

        # Text strings used with format_unicode are not changed.
        self.assertEqual(convert(format_unicode, u"text"), u"text")

        # Binary strings used with format_unicode are converted.
        self.assertEqual(convert(format_unicode, b"text"), u"text")

        # Binary strings used with format_text are not changed.
        self.assertEqual(convert(format_text, b"text"), b"text")

        # Test format_hdrop with existing file paths.
        with NamedTemporaryFile() as f1, NamedTemporaryFile() as f2:
            # Strings are converted to tuples containing file paths. Test
            # using Unicode and binary strings.
            # First, test using one existing file.
            for test_string in [u"%s\0\0", u"%s\n\n", u"%s\0", u"%s\n"]:
                test_string = test_string % f1.name
                f1name = u"%s" % f1.name
                self.assertEqual(convert(format_hdrop, test_string),
                                 (f1name,))
                test_string = test_string.encode()
                f1name = f1name.encode()
                self.assertEqual(convert(format_hdrop, test_string),
                                 (f1name,))

            # Then, test using two.
            for test_string in ["%s\0%s\0\0", "%s\n%s\0", "%s\n%s\n"]:
                test_string = test_string % (f1.name, f2.name)
                f1name, f2name = u"%s" % f1.name, u"%s" % f2.name
                self.assertEqual(convert(format_hdrop, test_string),
                                 (f1name, f2name))
                test_string = test_string.encode()
                f1name, f2name = f1name.encode(), f2name.encode()
                self.assertEqual(convert(format_hdrop, test_string),
                                 (f1name, f2name))

            # Tuples and lists containing strings are accepted. Lists are
            # converted to tuples.
            self.assertEqual(convert(format_hdrop, (f1.name,)), (f1.name,))
            self.assertEqual(convert(format_hdrop, [f1.name]), (f1.name,))

        # Existing relative file paths are not accepted.
        cwd = os.getcwd()
        try:
            # Make a temporary directory and enter it.
            tempdir = mkdtemp()
            os.chdir(tempdir)

            # Test the relative file path.
            with NamedTemporaryFile(dir=tempdir) as f:
                basename = u"%s" % os.path.basename(f.name)
                for test_obj in [basename, basename.encode(), [basename],
                                 (basename,)]:
                    self.assertRaises(ValueError, convert, format_hdrop,
                                      test_obj)
        finally:
            # Return to the original working directory and delete tempdir.
            os.chdir(cwd)
            os.rmdir(tempdir)

        # Errors are raised when unacceptable content is used with the text
        # formats or with format_hdrop.
        for test_obj in [object(), None, 0]:
            self.assertRaises(TypeError, convert, format_text, test_obj)
            self.assertRaises(TypeError, convert, format_unicode, test_obj)
            self.assertRaises(TypeError, convert, format_hdrop, test_obj)
            self.assertRaises(TypeError, convert, format_hdrop, (test_obj,))
            self.assertRaises(TypeError, convert, format_hdrop, [test_obj])
        for test_string in [u"", u"\n", u"\0", u"test\n", u"test\0"]:
            self.assertRaises(ValueError, convert, format_hdrop,
                              test_string)
            self.assertRaises(ValueError, convert, format_hdrop,
                              test_string.encode())

        # Empty lists/tuples are not acceptable format_hdrop content.
        self.assertRaises(ValueError, convert, format_hdrop, [])
        self.assertRaises(ValueError, convert, format_hdrop, ())

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

        # Test the method with clear=False (default).
        c.copy_from_system(clear=False)
        self.assertEqual(c.text, text)
        self.assertEqual(Clipboard.get_system_text(), text)

        # Test again with clear=True.
        c = Clipboard()
        c.copy_from_system(clear=True)
        self.assertEqual(c.text, text)
        self.assertEqual(Clipboard.get_system_text(), "")

        # Test formats=format_unicode.
        # Set the system clipboard before testing.
        text1 = u"unicode text"
        c1 = Clipboard(contents={format_unicode: text1})
        c1.copy_to_system()
        c2 = Clipboard()
        c2.copy_from_system(formats=format_unicode)
        self.assertTrue(c2.has_format(format_unicode))
        self.assertEqual(c2.get_format(format_unicode), text1)

        # Test formats=format_text.
        # Set the system clipboard before testing.
        text2 = b"text"
        c1 = Clipboard(contents={format_text: text2})
        c1.copy_to_system()
        c2 = Clipboard()
        c2.copy_from_system(formats=format_text)
        self.assertTrue(c2.has_format(format_text))
        self.assertEqual(c2.get_format(format_text), text2)

        # Test formats=(format_unicode, format_text).
        # Set the system clipboard before testing. Use the same string for
        # both formats so the test will work on all platforms.
        c1 = Clipboard(contents={format_text: b"text",
                                 format_unicode: u"text"})
        c1.copy_to_system()
        c2 = Clipboard()
        c2.copy_from_system(formats=(format_unicode, format_text))
        self.assertTrue(c2.has_format(format_unicode))
        self.assertEqual(c2.get_format(format_unicode), u"text")
        self.assertTrue(c2.has_format(format_text))
        self.assertEqual(c2.get_format(format_text), b"text")

    def test_copy_to_system(self):
        # Test with format_unicode.
        text1 = u"unicode text"
        c = Clipboard(contents={format_unicode: text1})
        c.copy_to_system(clear=True)
        self.assertEqual(Clipboard.get_system_text(), text1)

        # Test with format_text. Text string used deliberately here;
        # get_system_text() should returns those.
        text2 = u"text"
        c = Clipboard(contents={format_text: text2})
        c.copy_to_system(clear=True)
        self.assertEqual(Clipboard.get_system_text(), text2)

        # Test with text.
        text3 = u"testing"
        c = Clipboard(text=text3)
        c.copy_to_system(clear=True)
        self.assertEqual(Clipboard.get_system_text(), text3)

        # Test with an empty Clipboard instance.
        c = Clipboard()
        c.copy_to_system(clear=False)
        self.assertEqual(Clipboard.get_system_text(), text3)
        c.copy_to_system(clear=True)
        self.assertEqual(Clipboard.get_system_text(), u"")

    def test_get_available_formats(self):
        # Test with an empty Clipboard instance.
        c = Clipboard()
        self.assertEqual(c.get_available_formats(), [])

        # Test with one format.
        c = Clipboard(contents={format_unicode: u"unicode text"})
        self.assertEqual(c.get_available_formats(), [format_unicode])

        # Test with two formats.
        c = Clipboard(contents={format_unicode: u"unicode text",
                                format_text: u"text"})
        self.assertEqual(c.get_available_formats(), [format_unicode,
                                                     format_text],
                         "format_unicode should precede format_text")

        # Test with text formats and one custom format. The preferred text
        # format should be first on the list.
        format_custom = 0
        c = Clipboard(contents={format_custom: 123,
                                format_unicode: u"unicode text"})
        self.assertEqual(c.get_available_formats(), [format_unicode,
                                                     format_custom],
                         "format_unicode should precede format_custom")
        c = Clipboard(contents={format_custom: 123,
                                format_text: b"text"})
        self.assertEqual(c.get_available_formats(), [format_text,
                                                     format_custom],
                         "format_text should precede format_custom")

        # Test with no text format and one custom format.
        c = Clipboard(contents={format_custom: 123})
        self.assertEqual(c.get_available_formats(), [format_custom])

    def test_has_format(self):
        # Test with an empty Clipboard instance.
        c = Clipboard()
        self.assertFalse(c.has_format(format_unicode))
        self.assertFalse(c.has_format(format_text))
        self.assertFalse(c.has_format(format_hdrop))

        # Test with one format.
        c = Clipboard(contents={format_unicode: u"unicode text"})
        self.assertTrue(c.has_format(format_unicode))
        self.assertFalse(c.has_format(format_text))

        # Test with two formats.
        c = Clipboard(contents={format_unicode: u"unicode text",
                                format_text: u"text"})
        self.assertTrue(c.has_format(format_unicode))
        self.assertTrue(c.has_format(format_text))

    def test_get_format(self):
        # Test with an empty Clipboard instance.
        c = Clipboard()
        self.assertRaises(ValueError, c.get_format, format_unicode)
        self.assertRaises(ValueError, c.get_format, format_text)
        self.assertRaises(ValueError, c.get_format, format_hdrop)

        # Test with one format.
        text1 = u"unicode text"
        c = Clipboard(contents={format_unicode: text1})
        self.assertEqual(c.get_format(format_unicode), text1)
        self.assertRaises(ValueError, c.get_format, format_text)
        self.assertRaises(ValueError, c.get_format, format_hdrop)

        # Test with two formats.
        text2 = b"text"
        c = Clipboard(contents={format_unicode: text1,
                                format_text: text2})
        self.assertEqual(c.get_format(format_unicode), text1)
        self.assertEqual(c.get_format(format_text), text2)
        self.assertRaises(ValueError, c.get_format, format_hdrop)

        # Test with format_hdrop.
        with NamedTemporaryFile() as f:
            c = Clipboard(contents={format_hdrop: f.name})
            self.assertRaises(ValueError, c.get_format, format_unicode)
            self.assertRaises(ValueError, c.get_format, format_text)
            self.assertEqual(c.get_format(format_hdrop), (f.name,))

    def test_set_format(self):
        # Test with one format.
        text1 = u"unicode text"
        c = Clipboard()
        c.set_format(format_unicode, text1)
        self.assertTrue(c.has_format(format_unicode))
        self.assertEqual(c.get_format(format_unicode), text1)
        self.assertFalse(c.has_format(format_text))
        self.assertRaises(ValueError, c.get_format, format_text)

        # Test with two formats.
        text2 = b"text"
        c.set_format(format_text, text2)
        self.assertTrue(c.has_format(format_unicode))
        self.assertEqual(c.get_format(format_unicode), text1)
        self.assertTrue(c.has_format(format_text))
        self.assertEqual(c.get_format(format_text), text2)

        # Test with format_hdrop.
        with NamedTemporaryFile() as f:
            c.set_format(format_hdrop, f.name)
            self.assertTrue(c.has_format(format_unicode))
            self.assertTrue(c.has_format(format_text))
            self.assertTrue(c.has_format(format_hdrop))
            self.assertEqual(c.get_format(format_hdrop), (f.name,))

        # Setting a format to None removes the format's content from the
        # instance.
        c.set_format(format_text, None)
        self.assertFalse(c.has_format(format_text))
        self.assertRaises(ValueError, c.get_format, format_text)
        self.assertTrue(c.has_format(format_unicode))
        self.assertTrue(c.has_format(format_hdrop))
        c.set_format(format_unicode, None)
        self.assertFalse(c.has_format(format_unicode))
        self.assertRaises(ValueError, c.get_format, format_unicode)
        self.assertTrue(c.has_format(format_hdrop))
        c.set_format(format_hdrop, None)
        self.assertFalse(c.has_format(format_hdrop))
        self.assertRaises(ValueError, c.get_format, format_hdrop)

    def test_has_text(self):
        # Test with an empty Clipboard instance.
        c = Clipboard()
        self.assertFalse(c.has_text())

        # Test with format_unicode only.
        c = Clipboard(contents={format_unicode: u"unicode text"})
        self.assertTrue(c.has_text())

        # Test with both text formats.
        c = Clipboard(contents={format_unicode: u"unicode text",
                                format_text: b"text"})
        self.assertTrue(c.has_text())

        # Test with format_text only.
        c = Clipboard(contents={format_text: b"text"})
        self.assertTrue(c.has_text())

        # Test with format_hdrop only.
        with NamedTemporaryFile() as f:
            c = Clipboard(contents={format_hdrop: f.name})
            self.assertFalse(c.has_text())

    def test_set_text(self):
        c = Clipboard()
        text = "test"
        c.set_text(text)
        self.assertTrue(c.has_text())
        self.assertEqual(c.get_text(), text)
        self.assertEqual(c.text, text)

        # Setting the text to None clears the stored text.
        c.set_text(None)
        self.assertFalse(c.has_text())
        self.assertIsNone(c.get_text())

        # Test setting the text using the text property.
        c.text = text
        self.assertTrue(c.has_text())
        self.assertEqual(c.get_text(), text)
        self.assertEqual(c.text, text)

    def test_get_text(self):
        # Test with an empty Clipboard instance.
        c = Clipboard()
        self.assertIsNone(c.get_text())

        # Test with Unicode text.
        text1 = u"test"
        c.set_text(text1)
        self.assertEqual(c.get_text(), text1)

        # Test with text set to None.
        c.set_text(None)
        self.assertIsNone(c.get_text())

        # Test with binary text.
        text2 = b"test"
        c.set_text(text2)
        self.assertEqual(c.get_text(), text2)

        # Test with format_hdrop.
        with NamedTemporaryFile() as f:
            c = Clipboard(contents={format_hdrop: f.name})
            self.assertIsNone(c.get_text())

    def test_comparison(self):
        # Test with two empty Clipboard instances.
        self.assertEqual(Clipboard(), Clipboard())

        # Test with format_unicode.
        c1 = Clipboard(contents={format_unicode: u"unicode text"})
        c2 = Clipboard(contents={format_unicode: u"unicode text"})
        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, Clipboard())

        # Test with the same clipboard instance.
        self.assertEqual(c1, c1)

        # Test with both text formats.
        c1 = Clipboard(contents={format_unicode: u"unicode text",
                                 format_text: b"text"})
        c2 = Clipboard(contents={format_unicode: u"unicode text",
                                 format_text: b"text"})
        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, Clipboard())

        # Test with format_text only.
        c1 = Clipboard(contents={format_text: b"text"})
        c2 = Clipboard(contents={format_text: b"text"})
        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, Clipboard())

        # Test with different text formats.
        c1 = Clipboard(contents={format_unicode: u"unicode text"})
        c2 = Clipboard(contents={format_text: b"text"})
        self.assertNotEqual(c1, c2)

        # Test with format_hdrop only.
        with NamedTemporaryFile() as f:
            c1 = Clipboard(contents={format_hdrop: f.name})
            c2 = Clipboard(contents={format_hdrop: f.name})
            self.assertEqual(c1, c2)
            self.assertNotEqual(c1, Clipboard())
            self.assertNotEqual(c1, Clipboard(text="text"))

    def test_flexible_string_types(self):
        # This is similar to the clipboard format conversion that Windows
        # performs when necessary. The Clipboard class should do this
        # regardless of platform/implementation.

        # Binary strings used with format_unicode are converted for us.
        c = Clipboard(contents={format_unicode: b"text"})
        self.assertEqual(c.get_format(format_unicode), u"text")
        c = Clipboard()
        c.set_format(format_unicode, b"text")
        self.assertEqual(c.get_format(format_unicode), u"text")

        # Text strings used with format_text (ANSI) are converted for us.
        c = Clipboard(contents={format_text: u"text"})
        self.assertEqual(c.get_format(format_text), b"text")
        c = Clipboard()
        c.set_format(format_text, u"text")
        self.assertEqual(c.get_format(format_text), b"text")

    def test_non_ascii(self):
        text = u"""
        ૱ ꠸ ┯ ┰ ┱ ┲ ❗ ► ◄ Ă ă 0 1 2 3 4 5 6 7 8 9 Ǖ ǖ Ꞁ ¤ ­ Ð ¢ ℥ Ω ℧ K ℶ
        ℷ ℸ ⅇ ⅊ ⚌ ⚍ ⚎ ⚏ ⚭ ⚮ ⌀ ⏑ ⏒ ⏓ ⏔ ⏕ ⏖ ⏗ ⏘ ⏙ ⏠ ⏡ ⏦ ᶀ ᶁ ᶂ ᶃ ᶄ ᶆ ᶇ ᶈ
        ᶉ ᶊ ᶋ ᶌ ᶍ ᶎ ᶏ ᶐ ᶑ ᶒ ᶓ ᶔ ᶕ ᶖ ᶗ ᶘ ᶙ ᶚ ᶸ ᵯ ᵰ ᵴ ᵶ ᵹ ᵼ ᵽ ᵾ ᵿ
        """
        Clipboard.set_system_text(text)
        self.assertEqual(Clipboard.get_system_text(), text)

    def test_non_strings(self):
        # Using non-string objects for text formats raises errors.
        self.assertRaises(TypeError, Clipboard, {format_text: 0})
        self.assertRaises(TypeError, Clipboard, {format_unicode: 0})
        self.assertRaises(TypeError, Clipboard, {format_text: object()})
        self.assertRaises(TypeError, Clipboard, {format_unicode: object()})
        self.assertRaises(TypeError, Clipboard, {format_text: None})
        self.assertRaises(TypeError, Clipboard, {format_unicode: None})

        c = Clipboard()
        self.assertRaises(TypeError, c.set_text, 0)
        self.assertRaises(TypeError, c.set_text, object())
        self.assertRaises(TypeError, c.set_format, format_text, 0)
        self.assertRaises(TypeError, c.set_format, format_text, object())
        self.assertRaises(TypeError, c.set_format, format_unicode, 0)
        self.assertRaises(TypeError, c.set_format, format_unicode, object())
        self.assertRaises(TypeError, c.set_system_text, 0)
        self.assertRaises(TypeError, c.set_system_text, object())


if __name__ == '__main__':
    unittest.main()
