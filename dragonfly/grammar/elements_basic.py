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
   reference to a :class:`dragonfly.all.Rule` object; this element
   allows a rule to include (i.e. reference) another rule
 - :class:`ListRef` --
   reference to a :class:`dragonfly.all.List` object

The following *element* classes are built up out of the fundamental 
classes listed above:

 - :class:`Dictation` --
   free-form dictation; this element matches any words the speaker says,
   and includes facilities for formatting the spoken words with correct
   spacing and capitalization
 - :class:`DictListRef` --
   reference to a :class:`dragonfly.all.DictList` object; this element is 
   similar to the :class:`dragonfly.all.ListRef` element, except that it 
   returns the value associated with the spoken words instead of the 
   spoken words themselves


Class reference
----------------------------------------------------------------------------

"""


import types
from ..log       import get_log
from .rule_base  import Rule
from .list       import ListBase, DictList


#===========================================================================
# Element base class.

class ElementBase(object):
    """
        Base class for all other element classes.

        Constructor argument:
         - *name* (*str*, default: *None*) --
           the name of this element; can be used when interpreting
           complex recognition for retrieving elements by name.

    """

    name = "uninitialized"

    _log_decode = get_log("grammar.decode")
    _log_eval = get_log("grammar.eval")

    def __init__(self, name=None):
        if not name:
            name = None
        self.name = name

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        if self.name:   name_str = ", name=%r" % self.name
        else:           name_str = ""
        return "%s(...%s)" % (self.__class__.__name__, name_str)

    def _get_children(self):
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

    def dependencies(self):
        """
            Returns an iterable containing the dependencies of this
            element and of this element's children.

            The dependencies are the objects that are necessary
            for this element.  These include lists and other rules.

        """
        dependencies = []
        for c in self.children:
            dependencies.extend(c.dependencies())
        return dependencies

    def compile(self, compiler):
        raise NotImplementedError("Call to virtual method compile()"
                                  " in base class ElementBase")

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

    #-----------------------------------------------------------------------
    # Internal utility methods for use by derived classes.

    def _copy_sequence(self, sequence, name, item_types=None):
        """
            Check that a given object is a sequence, copy its contents
            into a new tuple, and check that each item is of a given type.

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

        For a recognition to match, all child elements must match
        the recognition in the order that they were given in the
        *children* constructor argument.

    """

    def __init__(self, children=(), name=None):
        ElementBase.__init__(self, name=name)
        self._children = self._copy_sequence(children,
                                             "children", ElementBase)

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def _get_children(self):
        return self._children

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def dependencies(self):
        dependencies = []
        for c in self._children:
            dependencies.extend(c.dependencies())
        return dependencies

    def gstring(self):
        return "(" \
             + " ".join(map(lambda e: e.gstring(), self._children)) \
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
            try: path[-1].next()
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

        Recognitions always match this element.  If the child element
        does match the recognition, then that result is used.
        Otherwise, this element itself does match but the child
        is not processed.

    """

    def __init__(self, child, name=None):
        ElementBase.__init__(self, name)

        if not isinstance(child, ElementBase):
            raise TypeError("Child of %s object must be an"
                            " ElementBase instance." % self)
        self._child = child
        self._greedy = True

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def _get_children(self):
        return (self._child, )

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def dependencies(self):
        return self._child.dependencies()

    def gstring(self):
        return "[" + self._child.gstring() + "]"

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
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
        return

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

        For a recognition to match, at least one of the child elements
        must match the recognition.  The first matching child is
        used.  Child elements are searched in the order they are given
        in the *children* constructor argument.

    """

    def __init__(self, children=(), name=None):
        ElementBase.__init__(self, name)
        self._children = self._copy_sequence(children,
                                             "children", ElementBase)

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def _get_children(self):
        return self._children

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def gstring(self):
        return "(" \
             + " | ".join(map(lambda e: e.gstring(), self._children)) \
             + ")"

    def dependencies(self):
        dependencies = []
        for c in self._children:
            dependencies.extend(c.dependencies())
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

        For a recognition to match, at least one of the child elements
        must match the recognition.  The first matching child is
        used.  Child elements are searched in the order they are given
        in the *children* constructor argument.

    """

    def __init__(self, child, min=1, max=None, name=None):
        if not isinstance(child, ElementBase):
            raise TypeError("Child of %s object must be an"
                            " ElementBase instance." % self)
        assert isinstance(min, int)
        assert max is None or isinstance(max, int)
        assert max is None or min < max

        self._child = child
        self._min = min
        if max is None: self._max = min + 1
        else:           self._max = max

        optional_length = self._max - self._min - 1
        if optional_length > 0:
            element = Optional(child)
            for index in xrange(optional_length):
                element = Optional(Sequence([child, element]))

            if self._min >= 1:
                children = [child] * self._min + [element]
            else:
                children = [element]
        elif self._min > 0:
            children = [child] * self._min
        else:
            raise ValueError("Repetition not allowed to be empty.")

        Sequence.__init__(self, children, name=name)

    def dependencies(self):
        return self._child.dependencies()

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
        for index in xrange(self._min):
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

    def __init__(self, text, name=None, value=None):
        ElementBase.__init__(self, name)
        self._value = value

        if not isinstance(text, (str, unicode)):
            raise TypeError("Text of %s object must be a"
                            " string." % self)
        self._words = text.split()

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        return "%s(%r)" % (self.__class__.__name__, self.words)

    words = property(lambda self: self._words)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def gstring(self):
        return " ".join(self._words)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        state.decode_attempt(self)

        # Iterate through this element's words.
        # If all match, success.  Else, failure.
        for i in xrange(len(self._words)):
            if state.word(i) != self._words[i]:
                state.decode_failure(self)
                return

        # All words matched, success.
        state.next(len(self._words))
        state.decode_success(self)
        yield state
        state.decode_retry(self)

        # Only one decoding possibility, failure on retry.
        state.decode_failure(self)
        return

    def value(self, node):
        if self._value is None: return " ".join(node.words())
        else: return self._value

#---------------------------------------------------------------------------

class RuleRef(ElementBase):

    def __init__(self, rule, name=None):
        ElementBase.__init__(self, name)

        if not isinstance(rule, Rule):
            raise TypeError("Rule object of %s object must be a"
                            " Dragonfly rule." % self)
        self._rule = rule

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        if not hasattr(self, "_rule"):
            return ElementBase.__str__(self)
        return '%s(%s)' % (self.__class__.__name__, self._rule.name)

    rule = property(lambda self: self._rule)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def dependencies(self):
        return [self._rule] + self._rule.dependencies()

    def gstring(self):
        return "<" + self._rule.name + ">"


    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        state.decode_attempt(self)

        # Allow the rule to attempt decoding.
        for result in self._rule.decode(state):
            state.decode_success(self)
            yield state
            state.decode_retry(self)

        # The rule failed to deliver a valid decoding, failure.
        state.decode_failure(self)
        return

    def value(self, node):
        return node.children[0].value()


#---------------------------------------------------------------------------

class ListRef(ElementBase):

    def __init__(self, name, list, key=None):
        ElementBase.__init__(self, name=name)

        if not isinstance(list, ListBase):
            raise TypeError("List object of %s object must be a"
                            " Dragonfly list." % self)
        self._list = list
        self._key = key

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        arguments = self._list.name
        if self._key: arguments += ", key=%r" % self._key
        return '%s(%s)' % (self.__class__.__name__, arguments)

    list = property(lambda self: self._list)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def dependencies(self):
        return [self._list]

    def compile(self, compiler):
        compiler.add_list(self._list.name)

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
        return

    def value(self, node):
        words = node.words()
        return " ".join(words)

#---------------------------------------------------------------------------

class DictListRef(ListRef):

    def __init__(self, name, dict, key=None):
        if not isinstance(dict, DictList):
            raise TypeError("Dict object of %s object must be a"
                            " Dragonfly DictList." % self)
        ListRef.__init__(self, name, dict, key)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def value(self, node):
        key = ListRef.value(self, node)
        return self._list[key]

#---------------------------------------------------------------------------

class Empty(ElementBase):

    def __init__(self, name=None):
        ElementBase.__init__(self, name)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def compile(self, compiler):
        pass

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
        return


#===========================================================================
# Slightly more complex element classes.

class Dictation(ElementBase):

    def __init__(self, name=None, format=True):
        ElementBase.__init__(self, name)
        self._format_words = format

    def __str__(self):
        if self.name:
            return "%s(%r)" % (self.__class__.__name__, self.name)
        else:
            return "%s()" % (self.__class__.__name__)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def gstring(self):
        return "<Dictation()>"

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def decode(self, state):
        state.decode_attempt(self)

        # Check that at least one word has been dictated, otherwise feel.
        if state.rule() != "dgndictation":
            state.decode_failure(self)
            return

        # Determine how many words have been dictated.
        count = 1
        while state.rule(count) == "dgndictation":
            count += 1

        # Yield possible states where the number of dictated words
        # gobbled is decreased by 1 between yields.
        for i in xrange(count, 0, -1):
            state.next(i)
            state.decode_success(self)
            yield state
            state.decode_retry(self)
            state.decode_rollback(self)

        # None of the possible states were accepted, failure.
        state.decode_failure(self)
        return

    def value(self, node):
        return node.engine.DictationContainer(node.words())


#---------------------------------------------------------------------------

class Impossible(ElementBase):

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

        state.decode_failure(self)
        return
