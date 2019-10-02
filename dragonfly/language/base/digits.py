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
This file implements base classes for structured number grammar
elements.

"""

from ..loader             import language
from ...grammar.elements  import Alternative, Repetition, Compound, RuleWrap


#---------------------------------------------------------------------------
# Base class for digit-series element classes.

class Digits(Repetition):

    _content = None
    _digit_name = "_digit"

    def __init__(self, name=None, min=1, max=12, as_int=False, default=None):
        if not self._content:
            self.__class__._content = language.DigitsContent
        self._digits = self._content.digits

        self._as_int = as_int
        if self._as_int: self._base = len(self._digits) - 1

        pairs = []
        for value, word in enumerate(self._digits):
            if isinstance(word, str):
                pairs.append((word, value))
            elif isinstance(word, (tuple, list)):
                pairs.extend([(w, value) for w in word])
            else:
                raise ValueError("Invalid type in digit list: %r" % word)

        alternatives = [Compound(w, value=v, name=self._digit_name)
                        for w, v in pairs]
        child = Alternative(alternatives)
        Repetition.__init__(self, child, min, max, name=name,
                            default=default)

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __repr__(self):
        arguments = "%d-%d" % (self._min, self._max)
        if self.name is not None:
            arguments = "'%s', %s" % (self.name, arguments)
        return "%s(%s)" % (self.__class__.__name__, arguments)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def value(self, node):
        children = node.get_children_by_name(self._digit_name)
        digits = [c.value() for c in children]
        if self._as_int:
            value = 0
            for d in digits:
                value *= self._base
                value += d
            return d
        else:
            return digits


#---------------------------------------------------------------------------
# Digits reference class.

class DigitsRef(RuleWrap):

    def __init__(self, name=None, min=1, max=12, as_int=True, default=None):
        element = Digits(name=None, min=min, max=max, as_int=as_int)
        RuleWrap.__init__(self, name, element, default=default)
