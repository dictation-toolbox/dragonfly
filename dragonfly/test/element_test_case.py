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
"""

import sys
import time
import unittest
import natlink
from dragonfly  import *
from ..test     import TestError


#===========================================================================

class _Unique(object): 
    """ Token class representing a unique identity. """

    def __init__(self, name):
        self._name = name

    def __str__(self):
        return self._name

    __repr__ = __str__


RecognitionFailure = _Unique("RecognitionFailure")


#===========================================================================

class ElementTestGrammar(Grammar):

    _log = get_log("ElementTestGrammar")

    _NotSet = _Unique("NoRecognition")

    def __init__(self, element):
        Grammar.__init__(self, "ElementTestGrammar")
#        prefix = Literal("Dragonfly Test")
#        root = Sequence([prefix, element])
#        root = element
#        test_rule = ElementTestRule("rule", root)
        self.add_rule(ElementTestRule("rule", element))

    def test(self, input_output):
        self.load()
        self.set_exclusiveness(True)
        try:
            for words, expected_result in input_output:
                if isinstance(words, basestring):
                    words = words.split()
                self._test_recognition(words, expected_result)
        finally:
            self.unload()

    def _test_recognition(self, words, expected_result):
        self._recognized_result = self._NotSet
#        words = ["Dragonfly", "Test"] + words
        try:
            self.engine.mimic(words)
        except natlink.MimicFailed:
            if expected_result == RecognitionFailure:
                self._log.debug("correct recognition failure")
                return
            else:
                self._log.exception("Mimic failed. (Words: %s)" % (words,))
                raise TestError("Mimic failed (Words: %s)" % (words,))
        recognized_result = self._recognized_result

        if recognized_result == self._NotSet:
            self._log.error("Recognition failure. (Words: %s)" % (words,))
            raise TestError("Recognition failure. (Words: %s)" % (words,))
        elif recognized_result != expected_result:
            self._log.error("Recognition failure: expected %s, recognized %s."
                            % (expected_result, recognized_result))
            raise TestError("Recognition failure: expected %s, recognized %s."
                            % (expected_result, recognized_result))
        else:
            self._log.debug("correct result: %s" % (recognized_result,))

    def process_recognition(self, node):
#        test_node = node.children[0].children[1]
        test_node = node.children[0]
        result = test_node.value()
        self._recognized_result = result


class ElementTestRule(Rule):

    exported = True

    def process_recognition(self, node):
        self.grammar.process_recognition(node)


#===========================================================================

class ElementTestCase(unittest.TestCase):
    """
        Test case class for easy testing of language elements.

        This class is usually used in one of the following two ways:
        #. Set the class attribute :attr:`_element`.
        #. Override the :meth:`_build_element` method.  By default, this
           method simply returns :attr:`_element`.

    """

    _element = None

    def _build_element(self):
        return self._element

    element = property(fget=lambda self: self._build_element(),
                       doc="Property that gives the element to be tested.")

    #-----------------------------------------------------------------------

    def __init__(self):
        unittest.TestCase.__init__(self)

    #-----------------------------------------------------------------------

    def test_element(self):

        natlink.natConnect()
        try:
            element = self.element
            if not element:
                return
            grammar = ElementTestGrammar(element)
            grammar.test(self.input_output)
        except TestError, e:
            self.fail(str(e))
        finally:
            natlink.natDisconnect()
