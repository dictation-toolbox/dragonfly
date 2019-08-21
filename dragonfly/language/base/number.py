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
Number language element class
============================================================================

"""

from ...grammar.elements  import Alternative, Repetition, Sequence, RuleWrap
from ..loader             import language
from .integer             import Integer


#---------------------------------------------------------------------------
# Number class.

class Number(Alternative):

    _int_max = 1000000
    _ser_len = 8

    def __init__(self, name=None, zero=False, default=None):
        name = str(name)
        int_name = "_Number_int_" + name
        if zero:  int_min = 0
        else:     int_min = 1
        single = Integer(None, int_min, self._int_max)

        ser_name = "_Number_ser_" + name
        item = Integer(None, 0, 100)
        if zero:
            series = Repetition(item, 1, self._ser_len)
        else:
            first = Integer(None, 1, 100)
            repetition = Repetition(item, 0, self._ser_len - 1)
            series = Sequence([first, repetition])

        children = [single, series]
        Alternative.__init__(self, children, name=name, default=default)

    def value(self, node):
        value = Alternative.value(self, node)

        if isinstance(value, list):
            items = []
            for item in value:
                if isinstance(item, list):
                    items.extend(item)
                else:
                    items.append(item)
            value = 0
            for item in items:
                if item < 10:  factor = 10
                else:          factor = 100
                value *= factor
                value += item

        return value


#---------------------------------------------------------------------------
# Number reference class.

class NumberRef(RuleWrap):

    def __init__(self, name=None, zero=False, default=None):
        element = Number(None, zero=zero)
        RuleWrap.__init__(self, name, element, default=default)
