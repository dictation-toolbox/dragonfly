# -*- encoding: utf-8 -*-
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
Test cases for the dictation container class for Natlink
============================================================================

"""

import unittest
from six import string_types, text_type

from dragonfly import *
from ..test import TestError, RecognitionFailure, ElementTester
from ..engines.base import DictationContainerBase
from ..engines.backend_natlink.dictation import NatlinkDictationContainer


#===========================================================================

class DictationTestCase(unittest.TestCase):
    """
        Unit testing class for dictation containers.

    """

    input_output = None
    engine = None
    language = None

    #-----------------------------------------------------------------------

    def test_element(self):
        if not self.input_output:
            return
        engine = get_engine()
        if engine.name != self.engine:
            return
        if engine.language != self.language:
            return

        element = Dictation("dictation")
        tester = ElementTester(element)

        failures = []
        try:
            for test_info in self.input_output:
                if len(test_info) == 2:
                    words, expected_value = test_info
                elif len(test_info) == 3:
                    words, expected_value, flags = test_info
                else:
                    raise TestError("Invalid test info: %s" % (test_info,))

                if isinstance(words, string_types):
                    words = words.split()

                recognized_value = tester.recognize(words)
                if isinstance(recognized_value, string_types):
                    recognized_value = text_type(recognized_value)
                elif isinstance(recognized_value, DictationContainerBase):
                    recognized_value = text_type(recognized_value)
                print("result:", recognized_value)
                if recognized_value != expected_value:
                    failures.append((words, expected_value,
                                     recognized_value))
        except TestError as e:
            self.fail(str(e))

        if failures:
            message = ["Recognition mismatches:"]
            for (words, expected_value, recognized_value) in failures:
                message.append("  expected %r, recognized %r (words: %r)"
                               % (expected_value, recognized_value, words))
            self.fail("\n".join(message))


#===========================================================================

class EnglishNatlinkDictationTestCase(DictationTestCase):
    engine       = "natlink"
    language     = "en"
    input_output = [
                    # Trivial words.
                    (u"non-existent-word",           RecognitionFailure),
                    (u"hello",                       u"hello"),
                    (u"hello world",                 u"hello world"),

                    # Capitalization.
                    (u"\\Cap hello",                  u"Hello"),
                    (u"hello \\Cap",                  u"hello"),
                    (u"\\Cap hello world",            u"Hello world"),
                    (u"hello \\Cap world",            u"hello World"),
                    (u"\\Caps-On hello world",        u"Hello World"),
                    (u"\\Caps-Off hello world",       u"hello world"),
                    (u"\\Caps-On hello \\Caps-Off world", u"Hello world"),
                    (u"\\All-Caps hello world",       u"HELLO world"),

                    # Spacing.
                    (u"\\No-Space hello",             u"hello"),
                    (u"hello \\No-Space world",       u"helloworld"),
                    (u"hello \\No-Space \\Cap world",  u"helloWorld"),
                    (u"hello \\Cap \\No-Space world",  u"helloWorld"),
                    (u"\\No-Space-On hello world",    u"helloworld"),
                    (u"\\No-Space-On hello \\No-Space-Off world", u"hello world"),

                    # Words with special formatting.
                    (u".\\full-stop hello world",     u".  Hello world"),
                    (u"hello .\\full-stop world",     u"hello.  World"),
                    (u"hello world .\\full-stop",     u"hello world."),
                    (u",\\comma hello world",         u", hello world"),
                    (u"hello ,\\comma world",         u"hello, world"),
                    (u"hello world ,\\comma",         u"hello world,"),
                    (u"(\\left-paren hello world",    u"(hello world"),
                    (u"hello (\\left-paren world",    u"hello (world"),
                    (u"hello world (\\left-paren",    u"hello world ("),
                    (u"-\\hyphen hello world",        u"-hello world"),
                    (u"hello -\\hyphen world",        u"hello-world"),
                    (u"hello world -\\hyphen",        u"hello world-"),
                    (u"four .\\point seven",          u"4.7"),
                    (u"four .\\dot seven",            u"4.7"),
                    (u"four .\\full-stop seven",      u"4.  7"),

                    # Characters with accents.
                    (u"Düsseldorf",                  u"Düsseldorf"),
                   ]


#===========================================================================

if __name__ == "__main__":
    import sys
    import nose
    loader = nose.loader.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules["__main__"])
    nose.core.TestProgram(suite=suite)
