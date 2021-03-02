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
Fundamental element classes
============================================================================

Dragonfly grammars are built up out of a small set of fundamental building
blocks.  These building blocks are implemented by the following *element*
classes:

 - :class:`ElementBase` --
   the base class from which all other element classes are derived
 - :class:`Sequence` --
   sequence of child elements which must all match in the order given
 - :class:`Alternative` --
   list of possibilities of which only one will be matched
 - :class:`Optional` --
   wrapper around a child element which makes the child element optional
 - :class:`Repetition` --
   repetition of a child element
 - :class:`Literal` --
   literal word which must be said exactly by the speaker as given
 - :class:`RuleRef` --
   reference to a :class:`dragonfly.grammar.rule_base.Rule` object;
   this element allows a rule to include (i.e. reference) another rule
 - :class:`ListRef` --
   reference to a :class:`dragonfly.grammar.list.List` object
 - :class:`Impossible` --
   a special element that cannot be recognized
 - :class:`Empty` --
   a special element that is always recognized

The following *element* classes are built up out of the fundamental
classes listed above:

 - :class:`Dictation` --
   free-form dictation; this element matches any words the speaker says,
   and includes facilities for formatting the spoken words with correct
   spacing and capitalization
 - :class:`Modifier` --
   modifies the output of another element by applying a function to it
   following recognition
 - :class:`DictListRef` --
   reference to a :class:`dragonfly.DictList` object; this element is
   similar to the :class:`dragonfly.ListRef` element, except that it returns
   the value associated with the spoken words instead of the spoken words
   themselves
 - :class:`RuleWrap` --
   an element class used to wrap a Dragonfly element into a new private
   rule to be referenced by the same element or other :class:`RuleRef`
   elements

See the following documentation sections for additional information and
usage examples:

 * :ref:`Elements (Object model section) <RefObjectModelElements>`
 * :ref:`RefElementBasicDocTests`

"""

# pylint: disable=abstract-method,no-self-use,too-many-lines
# Suppress a few warnings.

import copy
import itertools
import logging

from six import integer_types, string_types

from .rule_base  import Rule
from .list       import ListBase, DictList

#===========================================================================
# Element base class.

id_generator = itertools.count()

class ElementBase(object):
    """ Base class for all other element classes. """

    name = "uninitialized"

    _log_decode = logging.getLogger("grammar.decode")
    _log_eval = logging.getLogger("grammar.eval")

    def __init__(self, name=None, default=None):
        """
            Constructor argument:
             - *name* (*str*, default: *None*) --
               the name of this element; can be used when interpreting
               complex recognition for retrieving elements by name.
             - *default* (*object*, default: *None*) --
               the default value used if this element is optional and wasn't
               spoken

        """
        if not name:
            name = None
        self.name = name
        self._default = default
        self._id = next(id_generator)

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __repr__(self):
        if self.name:   name_str = ", name=%r" % self.name
        else:           name_str = ""
        return "%s(...%s)" % (self.__class__.__name__, name_str)

    def _get_children(self):
        """
            Returns an iterable of this element's children.

            This method is used by the :meth:`.children` property, and
            should be overloaded by any derived classes to give
            the correct children element.

            By default, this method returns an empty tuple.

        """
        return ()
    children = property(lambda self: self._get_children(),
                        doc="Iterable of child elements.  (Read-only)")

    def element_tree_string(self):
        """
            Returns a formatted multi-line string representing this
            element and its children.

        """
        indent = "  "
        tree = []
        stack = [(self, 0)]
        while stack:
            element, index = stack.pop()
            if index == 0:
                tree.append((element, len(stack)))
            if len(element.children) > index:
                stack.append((element, index + 1))
                stack.append((element.children[index], 0))
        lines = (indent*depth + str(element) for element, depth in tree)
        return "\n".join(lines)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def dependencies(self, memo):
        """
            Returns an iterable containing the dependencies of this
            element and of this element's children.

            The dependencies are the objects that are necessary
            for this element.  These include lists and other rules.

        """
        if self._id in memo:
            return []
        memo.add(self._id)
        dependencies = []
        for c in self.children:
            dependencies.extend(c.dependencies(memo))
        return dependencies

    def gstring(self):
        """
            Returns a formatted grammar string of the contents
            of this element and its children.

            The grammar string is of a format similar to that used
            by Natlink to define its grammars.

        """
        raise NotImplementedError("Call to virtual method gstring()"
                                  " in base class ElementBase")

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        """
            Attempt to decode the recognition stored in the given *state*.

        """
        raise NotImplementedError("Call to virtual method decode()"
                                  " in base class ElementBase")

    def value(self, node):
        """
            Determine the semantic value of this element given the
            recognition results stored in the *node*.

            Argument:
             - *node* --
               a :class:`dragonfly.grammar.state.Node` instance
               representing this element within the recognition
               parse tree

            The default behavior of this method is to return
            an iterable containing the recognized words matched
            by this element (i.e. *node.words()*).

        """
        return node.words()

    def has_default(self):
        """
        """
        return self._default is not None

    @property
    def default(self):
        """
        """
        return self._default

    #-----------------------------------------------------------------------
    # Internal utility methods for use by derived classes.

    def _copy_sequence(self, sequence, name, item_types=None):
        """
            Utility function for derived classes that checks that a given
            object is a sequence, copies its contents into a new tuple,
            and checks that each item is of a given type.

        """
        try:
            result = tuple(sequence)
        except TypeError:
            raise TypeError("%s object must be a sequence." % name)

        if not item_types: return result

        invalid = [c for c in result if not isinstance(c, item_types)]
        if invalid:
            raise TypeError("%s object must contain only %s types."
                            "  (Received %s)" % (name, item_types, result))
        return result


#===========================================================================
# Basic structural element classes.

class Sequence(ElementBase):
    """
        Element class representing a sequence of child elements
        which must all match a recognition in the correct order.

        Constructor arguments:
         - *children* (iterable, default: *()*) --
           the child elements of this element
         - *name* (*str*, default: *None*) --
           the name of this element
         - *default* (*object*, default: *None*) --
           the default value used if this element is optional and wasn't
           spoken

        For a recognition to match, all child elements must match
        the recognition in the order that they were given in the
        *children* constructor argument.

        Example usage::

           >>> from dragonfly.test import ElementTester
           >>> seq = Sequence([Literal("hello"), Literal("world")])
           >>> test_seq = ElementTester(seq)
           >>> test_seq.recognize("hello world")
           ['hello', 'world']
           >>> test_seq.recognize("hello universe")
           RecognitionFailure

    """

    def __init__(self, children=(), name=None, default=None):
        ElementBase.__init__(self, name=name, default=default)
        self._children = self._copy_sequence(children,
                                             "children", ElementBase)

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def _get_children(self):
        """ Returns the child elements contained within the sequence. """
        return self._children

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def dependencies(self, memo):
        if self._id in memo:
            return []
        memo.add(self._id)
        dependencies = []
        for c in self._children:
            dependencies.extend(c.dependencies(memo))
        return dependencies

    def gstring(self):
        return "(" \
             + " ".join([e.gstring() for e in self._children]) \
             + ")"

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        state.decode_attempt(self)

        # Special case for an empty sequence.
        if len(self._children) == 0:
            state.decode_success(self)
            yield state
            state.decode_retry(self)
            state.decode_failure(self)
            return

        # Attempt to walk a path through the entire sequence of children
        #  so that each one decodes successfully.
        path = [self._children[0].decode(state)]
        while path:
            # Allow the last child to attempt decoding.
            try: next(path[-1])
            except StopIteration:
                # Last child failed to decode, remove from path to
                #  allowed the one-before-last child to reattempt.
                path.pop()
            else:
                # Last child successfully decoded.
                if len(path) < len(self._children):
                    # Sequence not yet complete, append the next child.
                    path.append(self._children[len(path)].decode(state))
                else:
                    # Sequence complete, all children decoded successfully.
                    state.decode_success(self)
                    yield state
                    state.decode_retry(self)

        # Sequence of children could not all decode successfully: failure.
        state.decode_failure(self)
        return

    def value(self, node):
        """
            The *value* of a :class:`Sequence` is a list containing
            the values of each of its children.

        """
        return [child.value() for child in node.children]


#---------------------------------------------------------------------------

class Optional(ElementBase):
    """
        Element class representing an optional child element.

        Constructor arguments:
         - *child* (*ElementBase*) --
           the child element of this element
         - *name* (*str*, default: *None*) --
           the name of this element
         - *default* (*object*, default: *None*) --
           the default value used if this element is optional and wasn't
           spoken

        Recognitions always match this element.  If the child element
        does match the recognition, then that result is used.
        Otherwise, this element itself does match but the child
        is not processed.

    """

    def __init__(self, child, name=None, default=None):
        ElementBase.__init__(self, name, default=default)

        if not isinstance(child, ElementBase):
            raise TypeError("Child of %s object must be an"
                            " ElementBase instance." % self)
        self._child = child
        self._greedy = True

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def _get_children(self):
        """ Returns the optional child element. """
        return (self._child, )

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def dependencies(self, memo):
        if self._id in memo:
            return []
        memo.add(self._id)
        return self._child.dependencies(memo)

    def gstring(self):
        return "[" + self._child.gstring() + "]"

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        # pylint: disable=unused-variable
        state.decode_attempt(self)

        # If in greedy mode, allow the child to decode before.
        if self._greedy:
            for result in self._child.decode(state):
                state.decode_success(self)
                yield state
                state.decode_retry(self)

            # Rollback decoding so that the null-decode can be yielded.
            state.decode_rollback(self)

        # Yield the null-decode possibility.
        state.decode_success(self)
        yield state
        state.decode_retry(self)

        # If not in greedy mode, allow the child to decode after.
        if not self._greedy:
            for result in self._child.decode(state):
                state.decode_success(self)
                yield state
                state.decode_retry(self)

        # No more decoding possibilities available, failure.
        state.decode_failure(self)

    def value(self, node):
        """
            The *value* of a :class:`Optional` is the value of its child,
            if the child did match the recognition.  Otherwise the
            *value* is *None*.

        """
        if node.children:
            return node.children[0].value()
        else:
            return None


#---------------------------------------------------------------------------

class Alternative(ElementBase):
    """
        Element class representing several child elements of which only
        one will match.

        Constructor arguments:
         - *children* (iterable, default: *()*) --
           the child elements of this element
         - *name* (*str*, default: *None*) --
           the name of this element
         - *default* (*object*, default: *None*) --
           the default value used if this element is optional and wasn't
           spoken

        For a recognition to match, at least one of the child elements
        must match the recognition.  The first matching child is
        used.  Child elements are searched in the order they are given
        in the *children* constructor argument.

    """

    def __init__(self, children=(), name=None, default=None):
        ElementBase.__init__(self, name, default=default)
        self._children = self._copy_sequence(children,
                                             "children", ElementBase)

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def _get_children(self):
        """ Returns the alternative child elements. """
        return self._children

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def gstring(self):
        return "(" \
             + " | ".join([e.gstring() for e in self._children]) \
             + ")"

    def dependencies(self, memo):
        if self._id in memo:
            return []
        memo.add(self._id)
        dependencies = []
        for c in self._children:
            dependencies.extend(c.dependencies(memo))
        return dependencies

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        state.decode_attempt(self)

        # Special case for an empty list of alternatives.
        if len(self._children) == 0:
            state.decode_success(self)
            yield state
            state.decode_retry(self)
            state.decode_failure(self)
            return

        # Iterate through the children.
        for child in self._children:

            # Iterate through this child's possible decoding states.
            # pylint: disable=unused-variable
            for result in child.decode(state):
                state.decode_success(self)
                yield state
                state.decode_retry(self)

            # Rollback to the alternative's original state, so that the
            #  next child starts decoding without interference from the
            #  previous child.
            state.decode_rollback(self)

        # None of the children could decode successfully: failure.
        state.decode_failure(self)
        return

    def value(self, node):
        """
            The *value* of an :class:`Alternative` is the value of its
            child that matched the recognition.

        """
        return node.children[0].value()


#---------------------------------------------------------------------------

class Repetition(Sequence):
    """
        Element class representing a repetition of one child element.

        Constructor arguments:
         - *child* (*ElementBase*) --
           the child element of this element
         - *min* (*int*, default: *1*) --
           the minimum number of times that the child element must
           be recognized; may be 0
         - *max* (*int*, default: *None*) --
           the maximum number of times that the child element must
           be recognized; if *None*, the child element must be recognized
           exactly *min* times (i.e. *max = min + 1*)
         - *name* (*str*, default: *None*) --
           the name of this element
         - *default* (*object*, default: *None*) --
           the default value used if this element is optional and wasn't
           spoken
         - *optimize* (*bool*, default: *True*) --
           whether the engine's compiler should compile the element
           optimally

        For a recognition to match, at least one of the child elements
        must match the recognition.  The first matching child is
        used.  Child elements are searched in the order they are given
        in the *children* constructor argument.

        If the *optimize* argument is set to *True*, the compiler will
        ignore the *min* and *max* limits to reduce grammar complexity. If
        the number of repetitions recognized is more than the *max* value,
        the rule will fail to match.

    """

    # pylint: disable=redefined-builtin,unused-variable

    def __init__(self, child, min=1, max=None, name=None, default=None,
                 optimize=True):
        if not isinstance(child, ElementBase):
            raise TypeError("Child of %s object must be an"
                            " ElementBase instance." % self)
        assert isinstance(min, integer_types)
        assert max is None or isinstance(max, integer_types)
        assert max is None or min < max, "min must be less than max"

        self._child = child
        self._min = min
        if max is None: self._max = min + 1
        else:           self._max = max
        self._optimize = optimize

        optional_length = self._max - self._min - 1
        if optional_length > 0:
            element = Optional(child)
            for index in range(optional_length-1):
                element = Optional(Sequence([child, element]))

            if self._min >= 1:
                children = [child] * self._min + [element]
            else:
                children = [element]
        elif self._min > 0:
            children = [child] * self._min
        else:
            raise ValueError("Repetition not allowed to be empty.")

        Sequence.__init__(self, children, name=name, default=default)

    min = property(
        lambda self: self._min,
        doc="The minimum number of times that the child element must be "
        "recognized; may be 0. (Read-only)"
    )

    max = property(
        lambda self: self._max,
        doc="The maximum number of times that the child element must be "
        "recognized; if *None*, the child element must be "
        "recognized exactly *min* times (i.e. *max = min + 1*). "
        "(Read-only)"
    )

    optimize = property(
        lambda self: self._optimize,
        doc="Whether the engine's compiler should compile the element "
        "optimally. (Read-only)"
    )

    def dependencies(self, memo):
        if self._id in memo:
            return []
        memo.add(self._id)
        return self._child.dependencies(memo)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def get_repetitions(self, node):
        """
            Returns a list containing the nodes associated with
            each repetition of this element's child element.

            Argument:
             - *node* (*Node*) --
               the parse tree node associated with this repetition element;
               necessary for searching for child elements within the parse
               tree

        """
        repetitions = []
        for index in range(self._min):
            element = node.children[index]
            if element.actor != self._child:
                raise TypeError("Invalid child of %s: %s" \
                    % (self, element.actor))
            repetitions.append(element)

        if self._max - self._min > 1:
            optional = node.children[-1]
            while optional.children:
                child = optional.children[0]
                if isinstance(child.actor, Sequence):
                    assert len(child.children) == 2
                    element, optional = child.children
                    if element.actor != self._child:
                        raise TypeError("Invalid child of %s: %s" \
                            % (self, element.actor))
                    repetitions.append(element)
                elif child.actor == self._child:
                    repetitions.append(child)
                    break
                else:
                    raise TypeError("Invalid child of %s: %s" \
                        % (self, child.actor))

        return repetitions

    def value(self, node):
        """
            The *value* of a :class:`Repetition` is a list containing
            the values of its child.

            The length of this list is equal to the number of times
            that the child element was recognized.

        """
        repetitions = self.get_repetitions(node)
        return [r.value() for r in repetitions]


#---------------------------------------------------------------------------

class Literal(ElementBase):
    """
        Element class representing one or more literal words which must be
        said exactly by the speaker as given.

        Quoted words can be used to potentially improve accuracy. This
        currently only has an effect if using the Natlink SR engine
        back-end.

        Constructor arguments:
         - *text* (*str*) --
           the words to be said by the speaker
         - *name* (*str*, default: *None*) --
           the name of this element
         - *value* (*object*, default: *the recognized words*) --
           value returned when this element is successfully decoded
         - *default* (*object*, default: *None*) --
           the default value used if this element is optional and wasn't
           spoken
         - *quote_start_str* (*str*, default: \") --
           the string used for specifying the start of quoted words.
         - *quote_end_str* (*str*, default: \") --
           the string used for specifying the end of quoted words.
         - *strip_quote_strs* (*bool*, default: *True*) --
           whether the start and end quote strings should be stripped from
           this element's word lists.

    """

    def __init__(self, text, name=None, value=None, default=None,
                 quote_start_str='"', quote_end_str='"',
                 strip_quote_strs=True):
        ElementBase.__init__(self, name, default=default)
        self._value = value

        if not isinstance(text, string_types):
            raise TypeError("Text of %s object must be a"
                            " string." % self)

        # Construct the words and extended words lists. The latter includes
        # quoted words as single items.
        words = []
        words_ext = []
        current_quoted_sequence = []
        for word in text.split():
            # Begin quoted words.
            if word.startswith(quote_start_str):
                current_quoted_sequence.append(word)

            # End quoted words.
            elif current_quoted_sequence and word.endswith(quote_end_str):
                current_quoted_sequence.append(word)
                quoted_words = " ".join(current_quoted_sequence)

                # Strip quote start and end strings if specified.
                if strip_quote_strs:
                    quoted_words = quoted_words[len(quote_start_str):
                                                len(quote_end_str) * -1]

                # Add the words to both lists.
                words.extend(quoted_words.split())
                words_ext.append(quoted_words)

                # Clear current sequence list.
                del current_quoted_sequence[:]

            # Continuing quoted words.
            elif current_quoted_sequence:
                current_quoted_sequence.append(word)

            # Unquoted words.
            else:
                words.append(word)
                words_ext.append(word)

        # Handle unfinished quoted words sequence by treating it as normal.
        if current_quoted_sequence:
            words.extend(current_quoted_sequence)
            words_ext.extend(current_quoted_sequence)

        # Set both lists.
        self._words = words
        self._words_ext = words_ext

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.words)

    words = property(
        lambda self: self._words,
        doc="The words to be said by the speaker."
    )

    words_ext = property(
        lambda self: self._words_ext,
        doc="The words to be said by the speaker, with any quoted words as "
        "single items. This is extends the :py:attr:`~words` property."
    )

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def dependencies(self, memo):
        return []

    def gstring(self):
        return " ".join(self._words)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        state.decode_attempt(self)

        # Iterate through this element's words.
        # If all match, success.  Else, failure.
        if state.engine and state.engine.quoted_words_support:
            words = self._words_ext
        else:
            words = self._words
        for i in range(len(words)):
            word = state.word(i)

            # If word isn't None, make it lowercase.
            if word:
                word = word.lower()

            # If the words are not the same, then this is a decode failure.
            if word != words[i].lower():
                state.decode_failure(self)
                return

        # All words matched, success.
        state.next(len(words))
        state.decode_success(self)
        yield state
        state.decode_retry(self)

        # Only one decoding possibility, failure on retry.
        state.decode_failure(self)
        return

    def value(self, node):
        if self._value is None:
            return u" ".join(node.words())
        else:
            return self._value

#---------------------------------------------------------------------------

class RuleRef(ElementBase):
    """
        Element class representing a reference to another Dragonfly rule.

        Constructor arguments:
         - *rule* (*Rule*) --
           the Dragonfly rule to reference
         - *name* (*str*, default: *None*) --
           the name of this element
         - *default* (*object*, default: *None*) --
           the default value used if this element is optional and wasn't
           spoken

    """

    def __init__(self, rule, name=None, default=None):
        ElementBase.__init__(self, name, default=default)

        if not isinstance(rule, Rule):
            raise TypeError("Rule object of %s object must be a"
                            " Dragonfly rule." % self)
        self._rule = rule

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __repr__(self):
        if not hasattr(self, "_rule"):
            return ElementBase.__repr__(self)
        return '%s(%s)' % (self.__class__.__name__, self._rule.name)

    rule = property(lambda self: self._rule)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def dependencies(self, memo):
        if self._id in memo:
            return []
        memo.add(self._id)
        return [self._rule] + self._rule.dependencies(memo)

    def gstring(self):
        return "<" + self._rule.name + ">"


    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        state.decode_attempt(self)

        # Allow the rule to attempt decoding.
        # pylint: disable=unused-variable
        for result in self._rule.decode(state):
            state.decode_success(self)
            yield state
            state.decode_retry(self)

        # The rule failed to deliver a valid decoding, failure.
        state.decode_failure(self)

    def value(self, node):
        return node.children[0].value()


#---------------------------------------------------------------------------

class ListRef(ElementBase):
    """
        Element class representing a reference to a Dragonfly List.

        Constructor arguments:
         - *name* (*str*, default: *None*) --
           the name of this element
         - *list* (*ListBase*) --
           the Dragonfly List to reference
         - *key* (*object*, default: *None*) --
           key to differentiate between list references at runtime
         - *default* (*object*, default: *None*) --
           the default value used if this element is optional and wasn't
           spoken

    """

    # pylint: disable=redefined-builtin
    def __init__(self, name, list, key=None, default=None):
        self._list = None
        self._key = None

        ElementBase.__init__(self, name=name, default=default)

        if not isinstance(list, ListBase):
            raise TypeError("List argument to %s constructor must be a"
                            " Dragonfly list." % self.__class__.__name__)
        self._list = list
        self._key = key

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __repr__(self):
        arguments = []
        if self._list is not None:
            arguments.append(repr(self._list.name))
        if self._key:
            arguments.append("key=%r" % self._key)
        return "%s(%s)" % (self.__class__.__name__, ", ".join(arguments))

    list = property(lambda self: self._list)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def dependencies(self, memo):
        if self._id in memo:
            return []
        memo.add(self._id)
        return [self._list]

    def gstring(self):
        return "{" + self._list.name + "}"

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        state.decode_attempt(self)

        # If the next word(s) is/are in the list, success.
        delta = 0
        word = state.word()
        while 1:
            if word in self._list:
                state.next(delta + 1)
                state.decode_success(self)
                yield state
                state.decode_retry(self)
            delta += 1
            next = state.word(delta)
            if next is None:
                break
            word += " " + next

        # If the word is not in the list, or on retry, failure.
        state.decode_failure(self)

    def value(self, node):
        words = node.words()
        return " ".join(words)

#---------------------------------------------------------------------------

class DictListRef(ListRef):
    """
        Element class representing a reference to a Dragonfly DictList.

        Constructor arguments:
         - *name* (*str*, default: *None*) --
           the name of this element
         - *dict* (*DictList*) --
           the Dragonfly DictList to reference
         - *key* (*object*, default: *None*) --
           key to differentiate between list references at runtime
         - *default* (*object*, default: *None*) --
           the default value used if this element is optional and wasn't
           spoken

    """

    # pylint: disable=redefined-builtin
    def __init__(self, name, dict, key=None, default=None):
        if not isinstance(dict, DictList):
            raise TypeError("Dict object of %s object must be a Dragonfly "
                            "DictList." % self.__class__.__name__)
        ListRef.__init__(self, name, dict, key, default=default)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def value(self, node):
        key = ListRef.value(self, node)
        return self._list[key]

#---------------------------------------------------------------------------

class Empty(ElementBase):
    """
        Element class representing something that is always recognized.

        Constructor arguments:
         - *name* (*str*, default: *None*) --
           the name of this element
         - *value* (*object*, default: *True*) --
           value returned when this element is successfully decoded (always)

        Empty elements are equivalent to children of :class:`Optional`
        elements.

    """

    def __init__(self, name=None, value=True, default=None):
        self._value = value
        ElementBase.__init__(self, name, default=default)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def gstring(self):
        return "<Empty()>"

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        state.decode_attempt(self)

        state.decode_success(self)
        yield state
        state.decode_retry(self)

        state.decode_failure(self)

    def value(self, node):
        return self._value


#===========================================================================
# Slightly more complex element classes.

class Dictation(ElementBase):
    """
        Element class representing free dictation.

        Constructor arguments:
         - *name* (*str*, default: *None*) --
           the name of this element
         - *format* (*bool*, default: *True*) --
           whether the value returned should be a
           :class:`DictationContainerBase` object. If *False*, then the
           returned value is a list of the recognized words
         - *default* (*object*, default: *None*) --
           the default value used if this element is optional and wasn't
           spoken

        Returns a string-like :class:`DictationContainerBase` object
        containing the recognised words.
        By default this is formatted as a lowercase sentence.
        Alternative formatting can be applied by calling string methods like
        `replace` or `upper` on a :class:`Dictation` object, or by passing
        an arbitrary formatting function (taking and returning a string) to
        the `apply` method.

        Camel case text can be produced using the `camel` method. For
        example:

        .. code:: python

            str_func = lambda s: s.upper()
            Dictation("formattedtext").apply(str_func)
            Dictation("snake_text").lower().replace(" ", "_")
            Dictation("camelText").camel()
    """

    # pylint: disable=redefined-builtin
    def __init__(self, name=None, format=True, default=None):
        ElementBase.__init__(self, name, default=default)
        self._format_words = format
        self._string_methods = []

    def __repr__(self):
        if self.name:
            return "%s(%r)" % (self.__class__.__name__, self.name)
        else:
            return "%s()" % (self.__class__.__name__)

    def __getattr__(self, name):
        if isinstance(name, str) and name[:2] == name[-2:] == '__':
            # skip non-existing dunder method lookups
            raise AttributeError(name)
        def call(*args, **kwargs):
            self._string_methods.append((name, args, kwargs))
            return self
        return call

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def gstring(self):
        return "<Dictation()>"

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        state.decode_attempt(self)

        # Check that at least one word has been dictated, otherwise fail.
        if state.rule() != "dgndictation":
            state.decode_failure(self)
            return

        # Determine how many words have been dictated.
        count = 1
        while state.rule(count) == "dgndictation":
            count += 1

        # Yield possible states where the number of dictated words
        # gobbled is decreased by 1 between yields.
        for i in range(count, 0, -1):
            state.next(i)
            state.decode_success(self)
            yield state
            state.decode_retry(self)
            state.decode_rollback(self)

        # None of the possible states were accepted, failure.
        state.decode_failure(self)
        return

    def value(self, node):
        if self._format_words:
            return node.engine.DictationContainer(node.words(),
                                                  self._string_methods)
        else:
            return node.words()

#---------------------------------------------------------------------------

class Modifier(Alternative):
    """
        Element allowing direct modification of the output of another
        element at recognition time.

        Constructor arguments:
            - *element* (*Element*) -- The element to be recognised, e.g.
              :class:`Dictation` or :class:`Repetition`, with appropriate
              arguments passed.
            - *modifier* (*function*) -- A function to be applied to the
              value of this element when it is recognised.

        Examples:

        .. code:: python

            # Recognises an integer, returns the integer plus one
            Modifier(IntegerRef("plus1", 1, 20), lambda n: n+1)

            # Recognises a series of integers, returns them separated by
            # commas as a string
            int_rep = Repetition(IntegerRef("", 0, 10), min=1, max=5,
                                 name="num_seq")
            Modifier(int_rep, lambda r: ", ".join(map(str, r)))

    """
    def __init__(self, element, modifier=None):
        self._modifier = modifier
        Alternative.__init__(self, children=(element,), name=element.name,
                             default=element.default)

    def value(self, node):
        initial_value = Alternative.value(self, node)
        if self._modifier:
            return self._modifier(initial_value)
        else:
            return initial_value

#---------------------------------------------------------------------------

class Impossible(ElementBase):
    """
        Element class representing speech that cannot be recognized.

        Constructor arguments:
         - *name* (*str*, default: *None*) --
           the name of this element

        Using an :class:`Impossible` element in a Dragonfly rule makes it
        impossible to recognize via speech or mimicry.

    """

    def __init__(self, name=None):
        ElementBase.__init__(self, name)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def gstring(self):
        return "<Impossible()>"

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        state.decode_attempt(self)

        # Impossible elements always fail to decode.
        state.decode_failure(self)
        return

        # Turn this method into a generator by using 'yield'. This works
        # even though the statement is unreachable.
        # pylint: disable=unreachable
        yield state

    def value(self, node):
        return self


#---------------------------------------------------------------------------

class RuleWrap(RuleRef):
    """
        Element class to wrap a Dragonfly element into a new private rule
        to be referenced by this element or others.

        :class:`RuleWrap` is a sub-class of :class:`RuleRef`, so
        :class:`RuleWrap` elements can be used in the same way as
        :class:`RuleRef` elements.

        Constructor arguments:
         - *name* (*str*, default: *None*) --
           the name of this element
         - *element* (*Element*) --
           the Dragonfly element to be wrapped
         - *default* (*object*, default: *None*) --
           the default value used if this element is optional and wasn't
           spoken

        Examples:

        .. code:: python

           # For saying and processing a Choice element two times.
           letter = RuleWrap("letter1", Choice("", {
               "alpha": "a",
               "bravo": "b",
               "charlie": "c"
           }))
           letter_extras = [
               letter,
               RuleRef(letter.rule, "letter2"),
               RuleRef(letter.rule, "letter3")
           ]

    """

    _next_id = 0

    def __init__(self, name, element, default=None):
        rule_name = "_%s_%02d" % (self.__class__.__name__, RuleWrap._next_id)
        RuleWrap._next_id += 1
        rule = Rule(name=rule_name, element=element, exported=False)
        RuleRef.__init__(self, rule=rule, name=name, default=default)
