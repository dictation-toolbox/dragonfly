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

from six import text_type, string_types

from dragonfly.engines import get_engine, EngineBase
from dragonfly.engines.base.dictation import DictationContainerBase

#---------------------------------------------------------------------------


class TestEngineSapi5(unittest.TestCase):

    def test_get_engine_sapi5_is_usable(self):
        """ Verify that the sapi5 engine is usable. """
        engine = get_engine()
        self.assertTrue(isinstance(engine, EngineBase))
        self.assertTrue(engine.name.startswith("sapi5"))

        engine.speak("testing WSR")
        from dragonfly import Literal, Sequence
        from dragonfly.test import ElementTester
        seq = Sequence([Literal("hello"), Literal("world")])
        tester = ElementTester(seq, engine=engine)
        results = tester.recognize("hello world")
        self.assertEqual([u"hello", u"world"], results)

    def test_dictation(self):
        # Test dictation separately for SAPI5 because test_dictation.py
        # won't work with it.
        from dragonfly import Dictation, Literal, Sequence
        from dragonfly.test import ElementTester, RecognitionFailure
        seq = Sequence([Literal("hello"), Dictation("text")])
        tester = ElementTester(seq)

        # Test one word.
        results = tester.recognize("hello world")
        assert results[0] == "hello"

        # Verify recognition returned dictation result.
        dictation = results[1]
        if not isinstance(dictation, DictationContainerBase):
            message = (u"Expected recognition result to be a dictation"
                       u" container, but received %r"
                       % (repr(dictation).decode("windows-1252"),))
            self.fail(message.encode("windows-1252"))

        # Verifying dictation converts/encode successfully.
        self.assertEqual(str(dictation), "world")
        self.assertEqual(text_type(dictation), "world")
        self.assertTrue(isinstance(repr(dictation), string_types))

        # Test incomplete.
        results = tester.recognize("hello")
        assert results is RecognitionFailure

    def test_recognition_observers(self):
        # RecognitionObservers are a bit quirky for the sapi5 engines,
        # so the tests for them are repeated here to handle that.
        from dragonfly import (Integer, Literal, RecognitionHistory,
                               RecognitionObserver)
        from dragonfly.test import ElementTester, RecognitionFailure

        class RecognitionObserverTester(RecognitionObserver):
            """ RecognitionObserver class from the recobs doctests. """

            def __init__(self):
                RecognitionObserver.__init__(self)
                self.waiting = False
                self.words = None

            def on_begin(self):
                self.waiting = True

            def on_recognition(self, words):
                self.waiting = False
                self.words = words

            def on_failure(self):
                self.waiting = False
                self.words = False

        test_recobs = RecognitionObserverTester()
        test_recobs.register()
        results = test_recobs.waiting, test_recobs.words
        assert results == (False, None)

        # Test simple literal element recognitions.
        test_lit = ElementTester(Literal("hello world"))
        assert test_lit.recognize("hello world") == "hello world"
        results = test_recobs.waiting, test_recobs.words
        assert results == (False, (u'hello', u'world'))
        assert test_lit.recognize("hello universe") is RecognitionFailure
        results = test_recobs.waiting, test_recobs.words
        assert results == (False, False)

        # Test Integer element recognitions
        test_int = ElementTester(Integer(min=1, max=100))
        assert test_int.recognize("seven") == 7
        results = test_recobs.waiting, test_recobs.words
        assert results == (False, (u'seven',))
        assert test_int.recognize("forty seven") == 47
        results = test_recobs.waiting, test_recobs.words
        assert results == (False, (u'forty', u'seven'))
        assert test_int.recognize("one hundred") is RecognitionFailure
        results = test_recobs.waiting, test_recobs.words
        assert results == (False, False)
        assert test_lit.recognize("hello world") == u'hello world'

        # Now test RecognitionHistory.
        history = RecognitionHistory()
        assert test_lit.recognize("hello world") == u'hello world'

        # Not yet registered, so didn't receive previous recognition.
        assert history == []
        history.register()
        assert test_lit.recognize("hello world") == u'hello world'

        # Now registered, so should have received previous recognition.
        assert history == [(u'hello', u'world')]
        assert test_lit.recognize("hello universe") is RecognitionFailure

        # Failed recognitions are ignored, so history is unchanged.
        assert history == [(u'hello', u'world')]
        assert test_int.recognize("eighty six") == 86
        assert history == [(u'hello', u'world'), (u'eighty', u'six')]

        # The RecognitionHistory class allows its maximum length to be set.
        history = RecognitionHistory(3)
        history.register()
        assert history == []
        for i, word in enumerate(["one", "two", "three", "four", "five"]):
            assert test_int.recognize(word) == i + 1
        assert history == [(u'three',), (u'four',), (u'five',)]

        history = RecognitionHistory(1)
        history.register()
        assert history == []
        for i, word in enumerate(["one", "two", "three", "four", "five"]):
            assert test_int.recognize(word) == i + 1
        assert history == [(u'five',)]
