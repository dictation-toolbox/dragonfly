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
RecognitionObserver base class
==========================================================================

Test fixture initialization::

    >>> from dragonfly import *
    >>> from dragonfly.test import ElementTester
    >>> engine = get_engine()
    >>> engine.connect()


Tests for RecognitionObserver class
----------------------------------------------------------------------------

A class derived from RecognitionObserver which will be used here for
testing it::

    >>> class RecognitionObserverTester(RecognitionObserver):
    ...     def __init__(self):
    ...         RecognitionObserver.__init__(self)
    ...         self.waiting = False
    ...         self.words = None
    ...     def on_begin(self):
    ...         self.waiting = True
    ...     def on_recognition(self, words):
    ...         self.waiting = False
    ...         self.words = words
    ...     def on_failure(self):
    ...         self.waiting = False
    ...         self.words = False
    ...
    >>> test_recobs = RecognitionObserverTester()
    >>> test_recobs.register()
    >>> test_recobs.waiting, test_recobs.words
    (False, None)

Simple literal element recognitions::

    >>> test_lit = ElementTester(Literal("hello world"))
    >>> test_lit.recognize("hello world")
    'hello world'
    >>> test_recobs.waiting, test_recobs.words
    (False, ['hello', 'world'])
    >>> test_lit.recognize("hello universe")
    RecognitionFailure
    >>> test_recobs.waiting, test_recobs.words
    (False, False)


Integer element recognitions::

    >>> test_int = ElementTester(Integer(min=1, max=100))
    >>> test_int.recognize("seven")
    7
    >>> test_recobs.waiting, test_recobs.words
    (False, ['seven'])
    >>> test_int.recognize("forty seven")
    47
    >>> test_recobs.waiting, test_recobs.words
    (False, ['forty', 'seven'])
    >>> test_int.recognize("one hundred")
    RecognitionFailure
    >>> test_recobs.waiting, test_recobs.words
    (False, False)
    >>> test_lit.recognize("hello world")
    'hello world'


RecognitionHistory class
==========================================================================

Basic usage of the RecognitionHistory class::

    >>> history = RecognitionHistory()
    >>> test_lit.recognize("hello world")
    'hello world'
    >>> # Not yet registered, so didn't receive previous recognition.
    >>> history
    []
    >>> history.register()
    >>> test_lit.recognize("hello world")
    'hello world'
    >>> # Now registered, so should have received previous recognition.
    >>> history
    [['hello', 'world']]
    >>> test_lit.recognize("hello universe")
    RecognitionFailure
    >>> # Failed recognitions are ignored, so history is unchanged.
    >>> history
    [['hello', 'world']]
    >>> test_int.recognize("eighty six")
    86
    >>> history
    [['hello', 'world'], ['eighty', 'six']]

The RecognitionHistory class allows its maximum length to be set::

    >>> history = RecognitionHistory(3)
    >>> history.register()
    >>> history
    []
    >>> for i, word in enumerate(["one", "two", "three", "four", "five"]):
    ...     assert test_int.recognize(word) == i + 1
    >>> history
    [['three'], ['four'], ['five']]

The length must be a positive integer.  A length of 0 is not allowed::

    >>> history = RecognitionHistory(0)
    Traceback (most recent call last):
      ...
    ValueError: length must be a positive int or None, received 0.

Minimum length is 1::

    >>> history = RecognitionHistory(1)
    >>> history.register()
    >>> history
    []
    >>> for i, word in enumerate(["one", "two", "three", "four", "five"]):
    ...     assert test_int.recognize(word) == i + 1
    >>> history
    [['five']]


Test fixture cleanup
----------------------------------------------------------------------------


Test fixture cleanup::

    >>> test_recobs.unregister()
    >>> engine.disconnect()

"""

if __name__ == "__main__":
    import doctest
    doctest.testmod(report=True)
