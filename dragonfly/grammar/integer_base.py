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


import elements as elements_


#---------------------------------------------------------------------------
# Base class for numeric value element classes.

class NumBase(elements_.Alternative):

    _element_builders = ()

    def __init__(self, name=None, minimum=None, maximum=None):
        self._minimum = minimum; self._maximum = maximum
        children = self._build_children(minimum, maximum)
        elements_.Alternative.__init__(self, children, name=name)

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        if self.name is not None: arguments = ["'%s'" % self.name]
        else: arguments = []
        if self._minimum is not None or self._maximum is not None:
            arguments.append("%s" % self._minimum)
            arguments.append("%s" % self._maximum)
        return "%s(%s)" % (self.__class__.__name__, ",".join(arguments))

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def _build_children(self, minimum, maximum):
        children = [c.build_element(minimum, maximum) \
                        for c in self._element_builders]
        return [c for c in children if c]

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def evaluate(self, node, data):
        if self._log_eval: self._log_eval.debug( \
            "%s%s: evaluating %s" % ("  "*node.depth, self, node.words()))

        assert len(node.children) == 1
        if self.name:
            child = node.children[0]
            value = child.actor.value(child)
            if self._log_eval: self._log_eval.debug( \
                "%s%s: value %s" % ("  "*node.depth, self, value))
            data[self.name] = value

    def value(self, node):
        child = node.children[0]
        return child.actor.value(child)


#---------------------------------------------------------------------------
# Base class for numeric value element classes.

class DigitsBase(elements_.Repetition):

    _digits = None
    _digit_name = "_digit"

    def __init__(self, name=None, min=1, max=None):
        pairs = []
        for value, word in enumerate(self._digits):
            if isinstance(word, str):
                pairs.append((word, value))
            elif isinstance(word, (tuple, list)):
                pairs.extend([(w, value) for w in word])
            else:
                raise ValueError("Invalid type in digit list: %s" % word)

        alternatives = [_ValueLit(w, v, name= self._digit_name) for w, v in pairs]
        child = elements_.Alternative(alternatives)
        elements_.Repetition.__init__(self, child, min, max, name=name)

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        arguments = "%d-%d" % (self._min, self._max)
        if self.name is not None:
            arguments = "'%s', %s" % (self.name, arguments)
        return "%s(%s)" % (self.__class__.__name__, arguments)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def evaluate(self, node, data):
        if self._log_eval: self._log_eval.debug( \
            "%s%s: evaluating %s" % ("  "*node.depth, self, node.words()))

        assert len(node.children) == self._min + 1
        if self.name:
            repetitions = node.actor.get_repetitions(node)
            values = [child.children[0].actor.value(child)
                            for child in repetitions]
            if self._log_eval: self._log_eval.debug( \
                "%s%s: values %s" % ("  "*node.depth, self, values))
            data[self.name] = values

    def value(self, node):
        children = node.get_children_by_name(self._digit_name)
        digits = [c.value() for c in children]
        return digits


#---------------------------------------------------------------------------
# Numeric element builder classes.

class NumBuilderBase(object):

    def __init__(self):
        pass

    def build_element(self, minimum, maximum):
        raise NotImplementedError("Call to virtual method build_element()"
                                  " in base class NumBuilderBase")


class LitNumBuilder(NumBuilderBase):

    def __init__(self, words, values):
        self._words_values = zip(words, values)

    def build_element(self, minimum, maximum):
        elements = [(word, value)
                    for word, value in self._words_values
                    if minimum <= value < maximum]
        if len(elements) > 1:
            return _ValueLitMap(elements)
        elif len(elements) == 1:
            return _ValueLit(elements[0][0], elements[0][1])
        else: return None


class SetNumBuilder(NumBuilderBase):

    def __init__(self, set, prefix=None, suffix=None):
        self._set = set; self._prefix = prefix; self._suffix = suffix

    def build_element(self, minimum, maximum):
        element = self._build_range_set(self._set, minimum, maximum)
        if not element: return None
        elif not self._prefix and not self._suffix: return element
        elif not self._prefix: return _ValueSeq((element, self._suffix), 0)
        elif not self._suffix: return _ValueSeq((self._prefix, element), 1)
        else: return _ValueSeq((self._prefix, element, self._suffix), 1)

    def _build_range_set(self, set, minimum, maximum):
        # Iterate through the set allowing each item to build an element.
        children = [c.build_element(minimum, maximum) for c in set]
        children = [c for c in children if c]

        # Wrap up results appropriately.
        if not children: return None
        if len(children) == 1: return children[0]
        else: return _ValueAlt(children)


class MagnitudeNumBuilder(NumBuilderBase):

    def __init__(self, magnitude_element, magnitude,
                 multipliers, remainders, optional_multiplier = True):
        self._magnitude_element = magnitude_element
        self._magnitude = magnitude
        self._multipliers = multipliers
        self._remainders = remainders
        self._optional_multiplier = optional_multiplier

    def build_element(self, minimum, maximum):

        # Sanity check.
        if minimum >= maximum: return None

        # Calculate ranges of multipliers and remainders.
        first_multiplier = minimum / self._magnitude
        last_multiplier  = (maximum - 1) / self._magnitude + 1
        first_remainder  = minimum % self._magnitude
        last_remainder   = maximum % self._magnitude

        # Handle special case of only one possible multiplier value.
        if first_multiplier == last_multiplier - 1:
            return self._build_range(first_multiplier, last_multiplier,
                                     first_remainder, last_remainder)

        children = []

        # Build partial range for first multiplier value, if necessary.
        if first_remainder > 0:
            c = self._build_range(first_multiplier, first_multiplier + 1,
                                  first_remainder, self._magnitude)
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
                                  0, self._magnitude)
            if c: children.append(c)

        # Wrap up result as is appropriate.
        if len(children) == 0: return None
        elif len(children) == 1: return children[0]
        else: return _ValueAlt(children)

    def _build_range(self, first_multiplier, last_multiplier,
                           first_remainder, last_remainder):

        # Build range for multipliers.
        multipliers = self._build_range_set(
                        self._multipliers, first_multiplier, last_multiplier)
        if not multipliers: return None

        # Build range for remainders.
        remainders = self._build_range_set(
                        self._remainders, first_remainder, last_remainder)
        if not remainders: return None

        # Advanced language features.
        if self._optional_multiplier \
                    and first_multiplier <= 1 and last_multiplier > 1:
            multipliers = _ValueOpt(multipliers, 1)
        if first_remainder == 0:
            remainders = _ValueOpt(remainders, 0)

        # Build magnitude element.
        return _Magnitude(self._magnitude, multipliers,
                          self._magnitude_element, remainders)

    def _build_range_set(self, set, minimum, maximum):
        # Iterate through the set allowing each item to build an element.
        children = [c.build_element(minimum, maximum) for c in set]
        children = [c for c in children if c]

        # Wrap up results appropriately.
        if not children: return None
        if len(children) == 1: return children[0]
        else: return _ValueAlt(children)


#---------------------------------------------------------------------------
# Element classes used in numeric grammar constructions.

class _ValueLit(elements_.Literal):

    def __init__(self, word, value, name=None):
        elements_.Literal.__init__(self, word, name=name)
        self._value = value

    def value(self, node):
        return self._value
    def value(self, node):
        return self._value


class _ValueAlt(elements_.Alternative):

    def __init__(self, children):
        elements_.Alternative.__init__(self, children)

    def value(self, node):
        assert len(node.children) == 1
        child = node.children[0]
        return child.actor.value(child)


class _ValueLitMap(elements_.Alternative):

    def __init__(self, words_values):
        elements_.ElementBase.__init__(self)
        self._word_keys = [w for w, v in words_values]
        self._words = dict(words_values)
        children = [elements_.Literal(w) for w, v in words_values]
        elements_.Alternative.__init__(self, children)

    def __str__(self):
        return "%s('%s')" % (self.__class__.__name__,
                        "', '".join(self._word_keys))

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        state.decode_attempt(self)

        word = state.word()
        if word in self._words:
            state.next(1)
            state.decode_success(self)
            yield state
            state.decode_retry(self)

        state.decode_failure(self)
        return

    def value(self, node):
        word = node.words()[0]
        return self._words[word]


class _ValueSeq(elements_.Sequence):

    def __init__(self, children, index):
        elements_.Sequence.__init__(self, children)
        self._index = index

    def __str__(self):
        return "%s(index=%s)" % (self.__class__.__name__, self._index)

    def value(self, node):
        child = node.children[self._index]
        return child.actor.value(child)


class _ValueOpt(elements_.Optional):

    def __init__(self, child, value):
        elements_.Optional.__init__(self, child)
        self._value = value

    def __str__(self):
        return "%s(default=%s)" % (self.__class__.__name__, self._value)

    def value(self, node):
        if len(node.children) == 1:
            child = node.children[0]
            return child.actor.value(child)
        else:
            return self._value


class _Magnitude(elements_.Sequence):

    def __init__(self, magnitude, multiplier, word, remainder):
        if word:
            children = (multiplier, word, remainder)
            self._remainder_index = 2
        else:
            children = (multiplier, remainder)
            self._remainder_index = 1
        self._multiplier_index = 0
        elements_.Sequence.__init__(self, children)
        self._magnitude = magnitude

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._magnitude)

    def value(self, node):
        multiplier = node.children[self._multiplier_index]
        remainder = node.children[self._remainder_index]

        multiplier = multiplier.actor.value(multiplier)
        remainder = remainder.actor.value(remainder)

        return multiplier * self._magnitude + remainder
