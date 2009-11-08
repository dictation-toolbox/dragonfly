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
Sequence element class
==========================================================================

Test fixture initialization::

    >>> from dragonfly import *
    >>> from dragonfly.test import ElementTester
    >>> engine = get_engine()
    >>> engine.connect()


Sequence
----------------------------------------------------------------------------

Basic usage::

    >>> seq = Sequence([Literal("hello"), Literal("world")])
    >>> test_seq = ElementTester(seq)
    >>> test_seq.recognize("hello world")
    ['hello', 'world']


Sequence
----------------------------------------------------------------------------

Basic usage::

    >>> seq = Sequence([Literal("hello"), Literal("world")])
    >>> test_seq = ElementTester(seq)
    >>> test_seq.recognize("hello world")
    ['hello', 'world']
    >>> test_seq.recognize("hello universe")
    RecognitionFailure

Constructor arguments::

    >>> c1, c2 = Literal("hello"), Literal("world")
    >>> len(Sequence(children=[c1, c2]).children)
    2
    >>> Sequence(children=[c1, c2], name="sequence_test").name
    'sequence_test'
    >>> Sequence([c1, c2], "sequence_test").name
    'sequence_test'
    >>> Sequence("invalid_children_type")
    Traceback (most recent call last):
      ...
    TypeError: children object must contain only <class 'dragonfly.grammar.elements_basic.ElementBase'> types.  (Received ('i', 'n', 'v', 'a', 'l', 'i', 'd', '_', 'c', 'h', 'i', 'l', 'd', 'r', 'e', 'n', '_', 't', 'y', 'p', 'e'))


Test fixture cleanup::

    >>> engine.disconnect()

"""

if __name__ == "__main__":
    import doctest
    doctest.testmod()
