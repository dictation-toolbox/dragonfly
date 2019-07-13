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
from six import string_types, text_type

from dragonfly.engines.base.dictation   import DictationContainerBase
from dragonfly.grammar.elements         import Compound, Dictation
from dragonfly.test.element_testcase    import ElementTestCase
from dragonfly.test.element_tester      import ElementTester


#===========================================================================

class TestNonAsciiDictation(unittest.TestCase):

    def test_dictation_non_ascii(self):
        """ Test handling of non-ASCII characters in dictation. """

        def value_func(node, extras):
            return extras["text"]
        element = Compound("test <text>",
                           extras=[Dictation(name="text")],
                           value_func=value_func)
        tester = ElementTester(element)

        words = [u"test", u"touch�"]
        dictation = tester.recognize(words)

        # Verify recognition returned dictation result.
        if not isinstance(dictation, DictationContainerBase):
            message = (u"Expected recognition result to be a dictation"
                       u" container, but received %r"
                       % (repr(dictation).decode("windows-1252"),))
            self.fail(message.encode("windows-1252"))

        # Verifying dictation converts/encode successfully.
        self.assertEqual(str(dictation), "touch�")
        self.assertEqual(text_type(dictation), u"touch�")
        self.assertTrue(isinstance(repr(dictation), string_types))


class NonAsciiUnicodeDictationTestCase(ElementTestCase):
    """ Verify handling of non-ASCII characters in unicode dictation. """

    def _build_element(self):
        def value_func(node, extras):
            return text_type(extras["text"])
        return Compound("test <text>",
                        extras=[Dictation(name="text")],
                        value_func=value_func)

    input_output = [
                    (u"test dictation",     u"dictation"),
                    (u"test touch�",        u"touch�"),
                    (u"test jalape�o",      u"jalape�o"),
                   ]


class NonAsciiStrDictationTestCase(ElementTestCase):
    """ Verify handling of non-ASCII characters in str dictation. """

    def _build_element(self):
        def value_func(node, extras):
            return str(extras["text"])
        return Compound("test <text>",
                        extras=[Dictation(name="text")],
                        value_func=value_func)

    input_output = [
                    ("test dictation",     "dictation"),
                    ("test touch�",        "touch�"),
                    ("test jalape�o",      "jalape�o"),
                   ]


class FormattedDictationTestCase(ElementTestCase):
    """ Verify handling of string methods applied to Dictation objects """

    def _build_element(self):
        def value_func(node, extras):
            return str(extras["text"])
        return Compound("test <text>",
                        extras=[Dictation(name="text").upper().replace(" ", "/")],
                        value_func=value_func)

    input_output = [
                    ("test some random dictation", "SOME/RANDOM/DICTATION"),
                    ("test touch� jalape�o",       "TOUCH�/JALAPE�O"),
                   ]


class CamelDictationTestCase(ElementTestCase):
    """ Verify handling of camelCase formatting applied to Dictation objects """

    def _build_element(self):
        def value_func(node, extras):
            return str(extras["text"])
        return Compound("test <text>",
                        extras=[Dictation(name="text").camel()],
                        value_func=value_func)

    input_output = [
                    ("test some random dictation", "someRandomDictation"),
                    ("test touch� jalape�o",       "touch�Jalape�o"),
                   ]


class ApplyDictationTestCase(ElementTestCase):
    """ Verify handling of arbitrary formatting applied to Dictation objects using apply() """

    f = lambda self, s: "".join(
        "_".join(s.split(" ")[:-1] + [s.split(" ")[-1].upper()])
    )

    def _build_element(self):
        def value_func(node, extras):
            return str(extras["text"])
        return Compound("test <text>",
                        extras=[Dictation(name="text").apply(self.f)],
                        value_func=value_func)

    input_output = [
                    ("test some random dictation", "some_random_DICTATION"),
                    ("test touch� jalape�o",       "touch�_JALAPE�O"),
                   ]

#===========================================================================

if __name__ == "__main__":
    unittest.main()
