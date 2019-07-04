# -*- encoding: utf-8 -*-
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

import unittest

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
        engine.connect()
        self.engine = engine

    def tearDown(self):
        self.engine.disconnect()

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
        tester = ElementTester(Literal(u"Привет, как дела?"))

        # Test that strings and Unicode objects can be used.
        results = tester.recognize("Привет, как дела?")
        assert results == u"Привет, как дела?"
        results = tester.recognize(u"Привет, как дела?")
        assert results == u"Привет, как дела?"

        # Check that recognition failure is possible.
        results = tester.recognize(u"до свидания")
        assert results is RecognitionFailure
