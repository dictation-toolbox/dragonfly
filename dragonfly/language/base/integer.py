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
This file implements base classes for structured integer grammar
elements.

"""

from ..loader            import language
from ...grammar.elements import (Alternative, Sequence, Optional,
                                 Compound, ListRef, RuleWrap)
from ...grammar.list     import  List


#---------------------------------------------------------------------------
# Base class for integer element classes.

class Integer(Alternative):

    _content = None

    def __init__(self, name=None, min=None, max=None, default=None):
        if not self._content:
            self.__class__._content = language.IntegerContent
        self._builders = self._content.builders

        self._min = min; self._max = max
        children = self._build_children(min, max)
        Alternative.__init__(self, children, name=name, default=default)

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        arguments = []
        if self.name is not None:
            arguments = ["%r" % self.name]
        if self._min is not None or self._max is not None:
            arguments.append("%s" % self._min)
            arguments.append("%s" % self._max)
        return "%s(%s)" % (self.__class__.__name__, ",".join(arguments))

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def _build_children(self, min, max):
        children = [c.build_element(min, max)
                    for c in self._builders]
        return [c for c in children if c]


#---------------------------------------------------------------------------
# Integer reference class.

class IntegerRef(RuleWrap):

    def __init__(self, name, min, max, default=None):
        element = Integer(None, min, max)
        RuleWrap.__init__(self, name, element, default=default)
