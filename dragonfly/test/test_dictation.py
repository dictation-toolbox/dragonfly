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

import copy
import locale
import unittest

from six import string_types, text_type, binary_type

from dragonfly.engines.base.dictation   import DictationContainerBase
from dragonfly.engines                  import get_engine
from dragonfly.grammar.elements         import Compound, Dictation
from dragonfly.test.element_testcase    import ElementTestCase
from dragonfly.test.element_tester      import ElementTester


#===========================================================================
class DictationElementTestCase(ElementTestCase):

    input_output = []

    def test_element(self):
        # Translate all inputs and outputs to the preferred encoding for
        # recognition so that the tests can run on Windows or Linux.
        engine = get_engine()
        encoding = locale.getpreferredencoding()
        uppercase_dictation_required = engine.name in ['sphinx', 'text']

        def translate(string):
            # Any binary strings in this file will be encoded with
            # windows-1252 as per the specified source file encoding.
            if isinstance(string, binary_type):
                string = string.decode("windows-1252").encode(encoding)

            return string

        for i, (input, output) in enumerate(self.input_output):
            new_input = translate(input)
            new_output = translate(output)

            # Also map input dictation words to uppercase if necessary.
            if uppercase_dictation_required:
                words = new_input.split()
                new_input = ' '.join(
                    [words[0]] + [word.upper() for word in words[1:]]
                )

                # Manually uppercase the accented characters we use because
                # upper() doesn't do it for us. There's probably a better
                # way, but this will do.
                if isinstance(new_input, binary_type):
                    new_input = (new_input.replace("\xa9", "\x89")
                                 .replace("\xb1", "\x91"))

            self.input_output[i] = (new_input, new_output)

        ElementTestCase.test_element(self)


class TestNonAsciiDictation(unittest.TestCase):

    def test_dictation_non_ascii(self):
        """ Test handling of non-ASCII characters in dictation. """

        def value_func(node, extras):
            return extras["text"]
        element = Compound("test <text>",
                           extras=[Dictation(name="text")],
                           value_func=value_func)
        tester = ElementTester(element)
        words = [u"test", u"touché"]
        engine = get_engine()
        uppercase_dictation_required = engine.name in ['sphinx', 'text']
        if uppercase_dictation_required:
            words[1] = words[1].upper()
        dictation = tester.recognize(words)

        # Verify recognition returned dictation result.
        if not isinstance(dictation, DictationContainerBase):
            encoding = locale.getpreferredencoding()
            message = (u"Expected recognition result to be a dictation"
                       u" container, but received %r"
                       % (repr(dictation),))
            self.fail(message.encode(encoding))

        # Verifying dictation converts/encode successfully.
        string = "touché"
        if isinstance(string, binary_type):
            encoding = locale.getpreferredencoding()
            string = string.decode("windows-1252").encode(encoding)
        self.assertEqual(str(dictation), string)
        self.assertEqual(text_type(dictation), u"touché")
        self.assertTrue(isinstance(repr(dictation), string_types))


class NonAsciiUnicodeDictationTestCase(DictationElementTestCase):
    """ Verify handling of non-ASCII characters in unicode dictation. """

    def _build_element(self):
        def value_func(node, extras):
            return text_type(extras["text"])
        return Compound("test <text>",
                        extras=[Dictation(name="text")],
                        value_func=value_func)

    input_output = [
                    (u"test dictation",     u"dictation"),
                    (u"test touché",        u"touché"),
                    (u"test jalapeño",      u"jalapeño"),
                   ]


class NonAsciiStrDictationTestCase(DictationElementTestCase):
    """ Verify handling of non-ASCII characters in str dictation. """

    def _build_element(self):
        def value_func(node, extras):
            return str(extras["text"])
        return Compound("test <text>",
                        extras=[Dictation(name="text")],
                        value_func=value_func)

    input_output = [
                    ("test dictation",     "dictation"),
                    ("test touché",        "touché"),
                    ("test jalapeño",      "jalapeño"),
                   ]


class FormattedDictationTestCase(DictationElementTestCase):
    """ Verify handling of string methods applied to Dictation objects """

    def _build_element(self):
        def value_func(node, extras):
            return str(extras["text"])
        return Compound("test <text>",
                        extras=[Dictation(name="text").upper().replace(" ", "/")],
                        value_func=value_func)

    input_output = [
                    ("test some random dictation", "SOME/RANDOM/DICTATION"),
                    ("test touché jalapeño",       "TOUCHÉ/JALAPEÑO"),
                   ]


class CamelDictationTestCase(DictationElementTestCase):
    """ Verify handling of camelCase formatting applied to Dictation objects """

    def _build_element(self):
        def value_func(node, extras):
            return str(extras["text"])
        return Compound("test <text>",
                        extras=[Dictation(name="text").camel()],
                        value_func=value_func)

    input_output = [
                    ("test some random dictation", "someRandomDictation"),
                    ("test touché jalapeño",       "touchéJalapeño"),
                   ]


class ApplyDictationTestCase(DictationElementTestCase):
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
                    ("test touché jalapeño",       "touché_JALAPEÑO"),
                   ]


class DictationCopyTestCase(unittest.TestCase):

    def test_copy(self):
        """ Test that Dictation elements can be copied. """
        element = Dictation("text")
        self.assertIsNot(element, copy.copy(element))
        element = Dictation("text").camel()
        self.assertIsNot(element, copy.copy(element))

#===========================================================================

if __name__ == "__main__":
    unittest.main()
