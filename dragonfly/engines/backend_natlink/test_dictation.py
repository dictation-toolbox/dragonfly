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

    #-----------------------------------------------------------------------

    def test_element(self):
        element = Dictation("dictation")
        tester = ElementTester(element)

        try:
            for test_info in self.input_output:
                if len(test_info) == 2:
                    words, expected_value = test_info
                elif len(test_info) == 3:
                    words, expected_value, flags = test_info
                else:
                    raise TestError("Invalid test info: %s" % (test_info,))

                if isinstance(words, basestring):
                    words = words.split()

                recognized_value = tester.recognize(words)
                if isinstance(recognized_value, basestring):
                    recognized_value = unicode(recognized_value)
                elif isinstance(recognized_value, DictationContainerBase):
                    recognized_value = unicode(recognized_value)
                print "result:", recognized_value
                if recognized_value != expected_value:
                    raise TestError("Recognition mismatch: expected %r,"
                                    " recognized %r (words: %r)"
                                    % (expected_value, recognized_value,
                                       words))
        except TestError, e:
            self.fail(str(e))


#===========================================================================

class EnglishNatlinkDictationTestCase(DictationTestCase):
    engine       = "natlink"
    language     = "en"
    input_output = [
                    # Trivial words.
                    (ur"non-existent-word",           RecognitionFailure),
                    (ur"hello",                       ur"hello"),
                    (ur"hello world",                 ur"hello world"),

                    # Capitalization.
                    (ur"\Cap hello",                  ur"Hello"),
                    (ur"hello \Cap",                  ur"hello"),
                    (ur"\Cap hello world",            ur"Hello world"),
                    (ur"hello \Cap world",            ur"hello World"),
                    (ur"\Caps-On hello world",        ur"Hello World"),
                    (ur"\Caps-Off hello world",       ur"hello world"),
                    (ur"\Caps-On hello \Caps-Off world", ur"Hello world"),
                    (ur"\All-Caps hello world",       ur"HELLO world"),

                    # Characters with accents.
                    (ur"Düsseldorf",                  ur"Düsseldorf"),
                   ]


#===========================================================================

if __name__ == "__main__":
    import sys
    loader = nose.loader.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules["__main__"])
    nose.core.TestProgram(suite=suite)
