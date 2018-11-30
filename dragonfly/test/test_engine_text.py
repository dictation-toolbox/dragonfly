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

from dragonfly.engines import get_engine, EngineBase, EngineError
from dragonfly import Literal, Dictation, Sequence, Repetition
from dragonfly.engines.backend_text.dictation import TextDictationContainer
from dragonfly.test import ElementTester, RecognitionFailure


#---------------------------------------------------------------------------

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
        tester = ElementTester(Literal("hello world"))
        results = tester.recognize("hello world")
        assert results == "hello world"

        # Check that recognition failure is possible.
        results = tester.recognize("goodbye")
        assert results is RecognitionFailure

    def test_dictation(self):
        """ Verify that the text engine can mimic dictation. """
        tester = ElementTester(Dictation("text"))
        results = tester.recognize("hello world")
        assert isinstance(results, TextDictationContainer)
        assert results.format() == "hello world"

        # Check that an empty string results in recognition failure.
        results = tester.recognize("")
        assert results is RecognitionFailure

    def test_mixed_dictation(self):
        """ Verify that the text engine can mimic rules with Dictation and
            Literal elements. """
        seq = Sequence([Literal("hello"), Dictation("text")])
        tester = ElementTester(seq)
        results = tester.recognize("hello world")
        assert results[0] == "hello"
        assert isinstance(results[1], TextDictationContainer)
        assert results[1].format() == "world"

        # Check that strings not starting with "hello" result in recognition
        # failure.
        results = tester.recognize("goodbye world")
        assert results is RecognitionFailure

    def test_unicode_literals(self):
        """ Verify that the text engine can mimic literals using non-ascii
            characters. """
        tester = ElementTester(Literal(u"Привет, как дела?"))
        results = tester.recognize(u"Привет, как дела?")
        assert results == u"Привет, как дела?"

        # Check that recognition failure is possible.
        results = tester.recognize(u"Привет")
        assert results is RecognitionFailure
        results = tester.recognize(u"до свидания")
        assert results is RecognitionFailure

    def test_repetition(self):
        rep = Repetition(Sequence([Literal("hello"), Dictation("text")]))
        tester = ElementTester(rep)

        # Test with one repetition.
        results = tester.recognize("hello world")
        assert len(results) == 1
        assert results[0][0] == "hello"
        assert isinstance(results[0][1], TextDictationContainer)
        assert results[0][1].format() == "world"

        # Test with two repetitions.
        results = tester.recognize("hello world hello testing")
        assert len(results) == 2
        assert results[0][0] == "hello"
        assert isinstance(results[0][1], TextDictationContainer)
        assert results[0][1].format() == "world"
        assert results[1][0] == "hello"
        assert isinstance(results[1][1], TextDictationContainer)
        assert results[1][1].format() == "testing"

        # Check that incomplete repetitions result in recognition
        # failure.
        results = tester.recognize("hello")
        assert results is RecognitionFailure
        results = tester.recognize("hello world hello")
        assert results is RecognitionFailure
