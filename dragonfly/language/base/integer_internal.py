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

# pylint: disable=redefined-builtin,no-self-use,too-many-branches

import copy

from ...grammar.elements  import (Alternative, Sequence, Optional, RuleRef,
                                  Compound, ListRef, Literal, Impossible)
from ...grammar.list      import List


#---------------------------------------------------------------------------
# Numeric element builder classes.

class IntBuilderBase(object):

    def __init__(self, modifier_function=None, modifier_mode=None):
        if modifier_mode is None:
            modifier_mode = ModifiedPathsCollection.MODE_AUGMENT

        self._modifier_function = modifier_function
        self._modifier_mode = modifier_mode

    def build_element(self, min, max, memo=None):
        if memo is None:
            memo = {}

        # Check if an appropriate element already exists in the memo.
        #  If so, then return it.
        key = (id(self), min, max)
        if key in memo:
            return copy.copy(memo[key])

        # Otherwise, build the element, save it in the memo and return it.
        element = self._build_element(min, max, memo)
        memo[key] = element
        return element

    def _build_element(self, min, max, memo):
        raise NotImplementedError("Call to virtual method _build_element()"
                                  " in base class IntBuilderBase")

    def _build_modified_paths(self, children, memo):
        # pylint: disable=unused-argument
        if len(children) == 0:    return None
        if len(children) == 1:    root = children[0]
        else:                     root = Alternative(children)
        return ModifiedPathsCollection(root, self._modifier_function,
                                       self._modifier_mode)


class MapIntBuilder(IntBuilderBase):

    def __init__(self, mapping):
        self._mapping = mapping
        IntBuilderBase.__init__(self)

    def _build_element(self, min, max, memo):
        mapping_memo = {}
        children = []
        for spec, value in self._mapping.items():
            if min <= value < max:
                if spec in mapping_memo:
                    children.append(mapping_memo[spec])
                else:
                    element = Compound(spec=spec, value=value)
                    children.append(element)
                    mapping_memo[spec] = element
        if len(children) > 1:
            return Alternative(children)
        elif len(children) == 1:
            return children[0]
        else:
            return None


class CollectionIntBuilder(IntBuilderBase):

    def __init__(self, spec, set, modifier_function=None,
                 modifier_mode=None):
        self._spec = spec
        self._set = set
        IntBuilderBase.__init__(self, modifier_function, modifier_mode)

    def _build_element(self, min, max, memo):
        child = self._build_range_set(self._set, min, max, memo)
        if not child:
            return None
        child.name = "element"
        element = Collection(self._spec, child)
        return element

    def _build_range_set(self, set, min, max, memo):
        # Iterate through the set allowing each item to build an element.
        children = [c.build_element(min, max, memo) for c in set]
        children = [c for c in children if c]

        # Build modified path elements, if necessary.
        if self._modifier_function is not None:
            c = self._build_modified_paths(children, memo)
            if c:
                # Don't use other children if in modifier mode REPLACE.
                mode = self._modifier_mode
                if mode == ModifiedPathsCollection.MODE_REPLACE:
                    del children[:]

                # Add the ModifiedPathsCollection element.
                children.append(c)

        # Wrap up results appropriately.
        if not children:
            return None
        if len(children) == 1:
            return children[0]
        else:
            return Alternative(children)


class MagnitudeIntBuilder(IntBuilderBase):

    _empty_list = None

    @classmethod
    def _get_empty_list(cls):
        """ Class method to ensure only one empty list is created. """
        if cls._empty_list is None:
            cls._empty_list = List("_MagnitudeIntBuilder_empty")
        return cls._empty_list

    def __init__(self, factor, spec, multipliers, remainders,
                 modifier_function=None, modifier_mode=None):
        self._factor = factor
        self._spec = spec
        self._multipliers = multipliers
        self._remainders = remainders
        IntBuilderBase.__init__(self, modifier_function, modifier_mode)

    def _build_element(self, min, max, memo):

        # Sanity check.
        if min >= max: return None

        # Calculate ranges of multipliers and remainders.
        first_multiplier = int(min / self._factor)
        last_multiplier  = int((max - 1) / self._factor + 1)
        first_remainder  = min % self._factor
        last_remainder   = max % self._factor
        if last_remainder == 0:
            last_remainder = self._factor

        # Handle special case of only one possible multiplier value.
        if first_multiplier == last_multiplier - 1:
            return self._build_range(first_multiplier, last_multiplier,
                                     first_remainder, last_remainder, memo)

        children = []

        # Build partial range for first multiplier value, if necessary.
        if first_remainder > 0:
            c = self._build_range(first_multiplier, first_multiplier + 1,
                                  first_remainder, self._factor, memo)
            if c: children.append(c)
            first_multiplier += 1

        # Build partial range for last multiplier value, if necessary.
        if last_remainder > 0:
            c = self._build_range(last_multiplier - 1, last_multiplier,
                                  0, last_remainder, memo)
            if c: children.append(c)
            last_multiplier -= 1

        # Build range for multiplier values which have the full
        #  range of remainder values.
        if first_multiplier < last_multiplier:
            c = self._build_range(first_multiplier, last_multiplier,
                                  0, self._factor, memo)
            if c: children.append(c)

        # Build modified path elements, if necessary.
        if self._modifier_function is not None:
            c = self._build_modified_paths(children, memo)
            if c:
                # Don't use other children if in modifier mode REPLACE.
                mode = self._modifier_mode
                if mode == ModifiedPathsCollection.MODE_REPLACE:
                    del children[:]

                # Add the ModifiedPathsCollection element.
                children.append(c)

        # Wrap up result as is appropriate.
        if len(children) == 0:    return None
        elif len(children) == 1:  return children[0]
        else:                     return Alternative(children)

    def _build_range(self, first_multiplier, last_multiplier,
                     first_remainder, last_remainder, memo):

        # Build range for multipliers.
        multipliers = self._build_range_set(self._multipliers,
                                            first_multiplier,
                                            last_multiplier, memo)
        if not multipliers: return None

        # Build range for remainders.
        remainders = self._build_range_set(self._remainders,
                                           first_remainder,
                                           last_remainder, memo)
        if not remainders:
            empty = self._get_empty_list()
            remainders = ListRef("_MagnitudeIntBuilder_empty_ref", empty)

        # Build magnitude element.
        multipliers.name = "multiplier"
        remainders.name = "remainder"
        return Magnitude(self._factor, self._spec, multipliers, remainders)

    def _build_range_set(self, set, min, max, memo):
        # Iterate through the set allowing each item to build an element.
        children = [c.build_element(min, max, memo) for c in set]
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

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self._factor)

    def value(self, node):
        mul_node = node.get_child_by_name(self._mul.name, shallow=True)
        rem_node = node.get_child_by_name(self._rem.name, shallow=True)

        if mul_node:  multiplier = mul_node.value()
        else:         multiplier = self._mul_default
        if rem_node:  remainder  = rem_node.value()
        else:         remainder  = self._rem_default

        return multiplier * self._factor + remainder


class ModifiedPathsCollection(Alternative):

    # Collect and use paths to *augment* recognition of the given element
    #  (default).  Discards nil value or unchanged strings returned by the
    #  modifier function.
    MODE_AUGMENT = 1

    # Collect and use paths to *replace* recognition of the given element.
    #  Discards nil value strings returned by the modifier function.  Keeps
    #  unchanged path strings.
    MODE_REPLACE = 2

    def __init__(self, element, modifier_function, modifier_mode,
                 name=None):

        if not 0 < modifier_mode <= 2:
            raise ValueError("Invalid modifier mode: %d" % modifier_mode)

        # Generate element tree recognition paths and use them to create
        #  elements.
        children = []
        specs = set()
        for path in self._generate_paths(element):
            # Get a flat list of each word in this path.
            all_words = []
            for words in path:
                all_words.extend(words)

            # Get a spec using the modifier function.
            text = " ".join(all_words)
            spec = modifier_function(text)

            # Handle the result based on the specified modifier mode.
            if modifier_mode is self.MODE_AUGMENT:
                if not spec or text == spec:
                    continue
            elif modifier_mode is self.MODE_REPLACE:
                if not spec:
                    continue

            # Always skip duplicate specs.
            if spec in specs:
                continue

            # Initialize a new ModifiedPath element, passing the original
            #  element and words for decode-time calculation of the integer
            #  value.
            specs.add(spec)
            children.append(ModifiedPath(spec, all_words, element))

        # Initialize super class.
        Alternative.__init__(self, children=children, name=name)

    def _generate_sequence_paths(self, element, child_no):
        if child_no > len(element.children) - 1:
            yield []
            return

        child = element.children[child_no]
        next_child = child_no + 1
        for head in self._generate_paths(child):
            if None in head:
                continue
            for tail in self._generate_sequence_paths(element, next_child):
                yield head + tail

    def _generate_paths(self, element):
        if isinstance(element, Literal):
            yield [element.words]

        elif isinstance(element, ListRef):
            if len(element.list) == 0:
                # Impossible path.
                yield [None]
            else:
                # Generate paths from the list words.
                for word in element.list.get_list_items():
                    yield [word.split()]

        elif isinstance(element, Sequence):
            # Generate each complete path of the sequence.
            for path in self._generate_sequence_paths(element, 0):
                if None not in path:
                    yield path

        elif isinstance(element, Alternative):
            # Generate the paths of each alternative.
            for child in element.children:
                for path in self._generate_paths(child):
                    if None not in path:
                        yield path

        elif isinstance(element, Optional):
            # Generate the possible paths.
            # Optional element is not spoken.
            yield []

            # Optional element is spoken.
            for path in self._generate_paths(element.children[0]):
                if None not in path:
                    yield path

        elif isinstance(element, Impossible):
            # Impossible path.
            yield [None]

        elif isinstance(element, RuleRef):
            # Generate the possible paths from the referenced rule's element
            # tree.
            for path in self._generate_paths(element.rule.element):
                if None not in path:
                    yield path

        else:
            yield []


class ModifiedPath(Compound):

    def __init__(self, spec, words, orig_root_element, name=None):
        self._words = words
        self._orig_root_element = orig_root_element
        Compound.__init__(self, spec, name=name)

    def value(self, node):
        """
            The *value* of a :class:`ModifiedPath` is the *value*
            obtained by decoding the original words.

        """
        import dragonfly.grammar.state as state_
        words_rules = tuple((word, 0) for word in self._words)
        s = state_.State(words_rules, [], node.engine)
        s.initialize_decoding()
        for _ in self._orig_root_element.decode(s):
            if s.finished():
                root = s.build_parse_tree()
                return root.value()
        self._log_decode.error("CompoundWord %s: failed to decode original"
                               " words %r.", self, " ".join(self._words))
        return None


#---------------------------------------------------------------------------
# Integer content class.

class IntegerContentBase(object):
    builders = None
