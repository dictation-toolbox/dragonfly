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

import sys
import unittest
from six import text_type

from dragonfly        import *
from ..test           import TestError, RecognitionFailure
from .element_tester  import ElementTester


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

    def run(self, result=None):
        return unittest.TestCase.run(self, result)

    def test_element(self):
        element = self.element
        if not element:
            return

        tester = ElementTester(element)

        try:
            for words, expected_value in self.input_output:
                recognized_value = tester.recognize(words)
                if recognized_value != expected_value:
                    raise TestError(u"Recognition mismatch: input %r gave"
                                    u" recognition %r, instead of expected %r"
                                    % (words, recognized_value,
                                       expected_value))
        except TestError as e:
            self.fail(text_type(e))
