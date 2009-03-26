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


from dragonfly.grammar.elements import (Alternative, Sequence, Optional,
                                        Compound, ListRef)
from dragonfly.grammar.list     import  List


#---------------------------------------------------------------------------
# Base class for integer element classes.

class IntegerBase(Alternative):

    _builders = ()

    def __init__(self, name=None, min=None, max=None):
        self._min = min; self._max = max
        children = self._build_children(min, max)
        Alternative.__init__(self, children, name=name)

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
# Numeric element builder classes.

class IntBuilderBase(object):

    def __init__(self):
        pass

    def build_element(self, min, max):
        raise NotImplementedError("Call to virtual method build_element()"
                                  " in base class IntBuilderBase")


class MapIntBuilder(IntBuilderBase):

    def __init__(self, mapping):
        self._mapping = mapping

    def build_element(self, min, max):
        elements = [(spec, value)
                    for spec, value in self._mapping.iteritems()
                    if min <= value < max]
        if len(elements) > 1:
            children = [Compound(spec=spec, value=value)
                        for spec, value in elements]
            return Alternative(children)
        elif len(elements) == 1:
            return Compound(spec=elements[0][0], value=elements[0][1])
        else:
            return None


class CollectionIntBuilder(IntBuilderBase):

    def __init__(self, spec, set):
        self._spec = spec
        self._set = set

    def build_element(self, min, max):
        child = self._build_range_set(self._set, min, max)
        if not child:
            return None
        child.name = "element"
        element = Collection(self._spec, child)
        return element

    def _build_range_set(self, set, min, max):
        # Iterate through the set allowing each item to build an element.
        children = [c.build_element(min, max) for c in set]
        children = [c for c in children if c]

        # Wrap up results appropriately.
        if not children:
            return None
        if len(children) == 1:
            return children[0]
        else:
            return Alternative(children)


class MagnitudeIntBuilder(IntBuilderBase):

    def __init__(self, factor, spec, multipliers, remainders):
        self._factor = factor
        self._spec = spec
        self._multipliers = multipliers
        self._remainders = remainders

    def build_element(self, min, max):

        # Sanity check.
        if min >= max: return None

        # Calculate ranges of multipliers and remainders.
        first_multiplier = min / self._factor
        last_multiplier  = (max - 1) / self._factor + 1
        first_remainder  = min % self._factor
        last_remainder   = max % self._factor
        if last_remainder == 0:
            last_remainder = self._factor

        # Handle special case of only one possible multiplier value.
        if first_multiplier == last_multiplier - 1:
            return self._build_range(first_multiplier, last_multiplier,
                                     first_remainder, last_remainder)

        children = []

        # Build partial range for first multiplier value, if necessary.
        if first_remainder > 0:
            c = self._build_range(first_multiplier, first_multiplier + 1,
                                  first_remainder, self._factor)
            if c: children.append(c)
            first_multiplier += 1

        # Build partial range for last multiplier value, if necessary.
        if last_remainder > 0:
            c = self._build_range(last_multiplier - 1, last_multiplier,
                                  0, last_remainder)
            if c: children.append(c)
            last_multiplier -= 1

        # Build range for multiplier values which have the full
        #  range of remainder values.
        if first_multiplier < last_multiplier:
            c = self._build_range(first_multiplier, last_multiplier,
                                  0, self._factor)
            if c: children.append(c)

        # Wrap up result as is appropriate.
        if len(children) == 0:    return None
        elif len(children) == 1:  return children[0]
        else:                     return Alternative(children)

    def _build_range(self, first_multiplier, last_multiplier,
                           first_remainder, last_remainder):

        # Build range for multipliers.
        multipliers = self._build_range_set(self._multipliers,
                                            first_multiplier,
                                            last_multiplier)
        if not multipliers: return None

        # Build range for remainders.
        remainders = self._build_range_set(self._remainders,
                                           first_remainder,
                                           last_remainder)
        if not remainders:
            l = List("_MagnitudeIntBuilder_empty")
            remainders = ListRef("_MagnitudeIntBuilder_emptyref", l)

        # Build magnitude element.
        multipliers.name = "multiplier"
        remainders.name = "remainder"
        return Magnitude(self._factor, self._spec, multipliers, remainders)

    def _build_range_set(self, set, min, max):
        # Iterate through the set allowing each item to build an element.
        children = [c.build_element(min, max) for c in set]
        children = [c for c in children if c]

        # Wrap up results appropriately.
        if not children:
            return None
        if len(children) == 1:
            return children[0]
        else:
            return Alternative(children)


#---------------------------------------------------------------------------
# Element classes used in numeric grammar constructions.

class Collection(Compound):

    _element_name = "element"
    _default_value = None

    def __init__(self, spec, element, name=None):
        self._element = element
        Compound.__init__(self, spec, extras=[element], name=name)

    def value(self, node):
        child_node = node.get_child_by_name(self._element_name, shallow=True)

        if child_node:  return child_node.value()
        else:           return self._default_value


class Magnitude(Compound):

    _mul_default = 1
    _rem_default = 0

    def __init__(self, factor, spec, multiplier, remainder, name=None):
        self._factor = factor
        self._mul = multiplier
        self._rem = remainder
        Compound.__init__(self, spec, extras=[multiplier, remainder], name=name)

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._factor)

    def value(self, node):
        mul_node = node.get_child_by_name(self._mul.name, shallow=True)
        rem_node = node.get_child_by_name(self._rem.name, shallow=True)

        if mul_node:  multiplier = mul_node.value()
        else:         multiplier = self._mul_default
        if rem_node:  remainder  = rem_node.value()
        else:         remainder  = self._rem_default

        return multiplier * self._factor + remainder
