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
from dragonfly        import *
from ...test          import TestError, RecognitionFailure, ElementTester
from ..base           import DictationContainerBase
from .dictation       import NatlinkDictationContainer


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

                if isinstance(words, str):
                    words = words.split()

                recognized_value = tester.recognize(words)
                if isinstance(recognized_value, str):
                    recognized_value = str(recognized_value)
                elif isinstance(recognized_value, DictationContainerBase):
                    recognized_value = str(recognized_value)
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
                    (r"non-existent-word",           RecognitionFailure),
                    (r"hello",                       r"hello"),
                    (r"hello world",                 r"hello world"),

                    # Capitalization.
                    (r"\Cap hello",                  r"Hello"),
                    (r"hello \Cap",                  r"hello"),
                    (r"\Cap hello world",            r"Hello world"),
                    (r"hello \Cap world",            r"hello World"),
                    (r"\Caps-On hello world",        r"Hello World"),
                    (r"\Caps-Off hello world",       r"hello world"),
                    (r"\Caps-On hello \Caps-Off world", r"Hello world"),
                    (r"\All-Caps hello world",       r"HELLO world"),

                    # Spacing.
                    (r"\No-Space hello",             r"hello"),
                    (r"hello \No-Space world",       r"helloworld"),
                    (r"hello \No-Space \Cap world",  r"helloWorld"),
                    (r"hello \Cap \No-Space world",  r"helloWorld"),
                    (r"\No-Space-On hello world",    r"helloworld"),
                    (r"\No-Space-On hello \No-Space-Off world", r"hello world"),

                    # Words with special formatting.
                    (r".\full-stop hello world",     r".  Hello world"),
                    (r"hello .\full-stop world",     r"hello.  World"),
                    (r"hello world .\full-stop",     r"hello world."),
                    (r",\comma hello world",         r", hello world"),
                    (r"hello ,\comma world",         r"hello, world"),
                    (r"hello world ,\comma",         r"hello world,"),
                    (r"(\left-paren hello world",    r"(hello world"),
                    (r"hello (\left-paren world",    r"hello (world"),
                    (r"hello world (\left-paren",    r"hello world ("),
                    (r"-\hyphen hello world",        r"-hello world"),
                    (r"hello -\hyphen world",        r"hello-world"),
                    (r"hello world -\hyphen",        r"hello world-"),
                    (r"four .\point seven",          r"4.7"),
                    (r"four .\dot seven",            r"4.7"),
                    (r"four .\full-stop seven",      r"4.  7"),

                    # Characters with accents.
                    (r"Düsseldorf",                  r"Düsseldorf"),
                   ]


#===========================================================================

if __name__ == "__main__":
    import sys
    loader = nose.loader.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules["__main__"])
    nose.core.TestProgram(suite=suite)
