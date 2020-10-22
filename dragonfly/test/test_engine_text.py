# -*- encoding: windows-1252 -*-
#
# This file is part of Dragonfly.
# (c) Copyright 2018 by Dane Finlay
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

import locale
import unittest

import six

from dragonfly.engines import EngineBase
from dragonfly import (Literal, Dictation, Sequence, CompoundRule,
                       get_engine)
from dragonfly.test import ElementTester, RecognitionFailure, RuleTestCase


# --------------------------------------------------------------------------

class TestEngineText(unittest.TestCase):

    def setUp(self):
        engine = get_engine("text")
        assert isinstance(engine, EngineBase)
        assert engine.name == "text"
        self.engine = engine

    def test_literal(self):
        """ Verify that the text engine is usable. """
        self.engine.speak("testing text")
        tester = ElementTester(Literal("hello world"))
        results = tester.recognize("hello world")
        assert results == "hello world"

        # Check that recognition failure is possible.
        results = tester.recognize("goodbye")
        assert results is RecognitionFailure

    def test_unicode_literals(self):
        """ Verify that the text engine can mimic literals using non-ascii
            characters. """
        tester = ElementTester(Literal(u"touché"))

        # Test that strings and Unicode objects can be used.
        string = "touché"
        if isinstance(string, six.binary_type):
            encoding = locale.getpreferredencoding()
            string = string.decode("windows-1252").encode(encoding)
        results = tester.recognize(string)
        assert results == u"touché"
        results = tester.recognize(u"touché")
        assert results == u"touché"

        # Check that recognition failure is possible.
        results = tester.recognize(u"jalapeño")
        assert results is RecognitionFailure
