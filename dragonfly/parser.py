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
    This file implements a simple input stream parser.
"""


import string


class ParserError(Exception):
    pass


class Parser(object):

    def __init__(self, parser_element, log=None):
        self._parser_element = parser_element
        self._log = log

    def parse(self, input, must_finish=True):
        state = State(input, log=self._log)
        generator = self._parser_element.parse(state)
        for result in generator:
            if not must_finish or state.finished():
                # Parse complete, return result.
                node = state.build_parse_tree()
                return node.value()
        # Failed to parse.
        return None

    def parse_multiple(self, input, must_finish=True):
        state = State(input, log=self._log)
        generator = self._parser_element.parse(state)

        values = []
        for result in generator:
            if not must_finish or state.finished():
                values.append(state.build_parse_tree().value())
        return values

#       return [state.build_parse_tree().value()
#           for result in generator
#           if not must_finish or state.finished()]


class State(object):

    #-----------------------------------------------------------------------
    # Methods for initialization.

    def __init__(self, data, index=0, log=None):
        self._data = data
        self._index = index
        self._log = log
        self._stack = []
        self._depth = 0
        self.initialize_decoding()

    def initialize_decoding(self):
        self._depth = 0
        self._stack = []
        self._previous_index = None

    def __str__(self):
        return self.position_string()

    #-----------------------------------------------------------------------
    # Methods for accessing recognition content.

    def position_string(self, width = 20, width_before = 6):
        mark = ">>"; continuation = "."
        width -= 2

        # Locate edges.
        i1 = self._index - width_before
        i2 = self._index - width_before + width - len(mark)

        # Account for edge effects.
        if i1 < 0:
            i2 = min(i2 - i1, len(self._data))
            i1 = 0
        elif i2 > len(self._data):
            width_before += i2 - len(self._data)
            i1 = max(i1 - i2 + len(self._data), 0)
            i2 = len(self._data)

        # Collect character representations.
        before = [repr(c)[1:-1] for c in self._data[i1:self._index]]
        after = [repr(c)[1:-1] for c in self._data[self._index:i2]]

        # Build before string.
        if i1 == 0 and len("".join(before)) <= width_before:
            before = '"' + "".join(before)
        else:
            while before and len("".join(before)) > width_before - 2:
                before.pop(0)
            before = "".join(before)
            before = '%s"%s' % (continuation * (width_before - len(before)), before)

        # Build after string.
        width_after = width - len(before) - len(mark)
        if i2 == len(self._data) and len("".join(after)) <= width_after:
            after = "".join(after) + '"'
        else:
            while after and len("".join(after)) > width_after - 2:
                after.pop()
            after = "".join(after)
            after = '%s"%s' % (after, continuation * (width_after - len(after)))

        # Build and return result.
        return '%s%s%s' % (before, mark, after)

    #-----------------------------------------------------------------------
    # Methods for parsing of input.

    def remaining(self):
        return len(self._data) - self._index

    def finished(self):
        return (len(self._data) - self._index) <= 0

    def peek(self, length):
        if self._index == len(self._data):
            return None
        elif self._index + length > len(self._data):
            length = len(self._data) - self._index
        return self._data[self._index : self._index + length]

    def next(self, length):
        if self._index == len(self._data):
            return None
        elif self._index + length > len(self._data):
            length = len(self._data) - self._index
        self._index += length
        return self._data[self._index - length : self._index]

    def build_parse_tree(self):
        root, index = self._build_parse_node(0, None)
        return root

    def _build_parse_node(self, index, parent):
        frame = self._stack[index]
        node = Node(parent, frame.actor, self._data,
                    frame.begin, frame.end, frame.depth)
        if parent: parent.add_child(node)
        index += 1
        while index < len(self._stack):
            if self._stack[index].depth != frame.depth + 1:
                break
            child, index = self._build_parse_node(index, node)
        return (node, index)

    #-----------------------------------------------------------------------
    # Methods for tracking parsing of input.

    class _Frame(object):
        __slots__ = ("depth", "actor", "begin", "end")
        def __init__(self, depth, actor, begin):
            self.depth = depth; self.actor = actor
            self.begin = begin; self.end = None

    def decode_attempt(self, element):
        assert isinstance(element, ParserElementBase)
        self._depth += 1
        self._stack.append(State._Frame(self._depth, element, self._index))
        self._log_step(element, "attempt")

    def decode_retry(self, element):
        assert isinstance(element, ParserElementBase)
        frame = self._get_frame_from_actor(element)
        self._depth = frame.depth
        self._log_step(element, "retry")

    def decode_rollback(self, element):
        assert isinstance(element, ParserElementBase)
        frame = self._get_frame_from_depth()
        if not frame or frame.actor != element:
            raise grammar_.GrammarError("Parser decoding stack broken")
        if frame is self._stack[-1]:
            # Last parser on the stack, rollback.
            self._index = frame.begin
        else:
            raise grammar_.GrammarError("Parser decoding stack broken")
        self._log_step(element, "rollback")

    def decode_success(self, element):
        assert isinstance(element, ParserElementBase)
        self._log_step(element, "success")
        frame = self._get_frame_from_depth()
        if not frame or frame.actor != element:
            raise grammar_.GrammarError("Parser decoding stack broken.")
        frame.end = self._index
        self._depth -= 1

    def decode_failure(self, element):
        assert isinstance(element, ParserElementBase)
        frame = self._stack.pop()
        self._index = frame.begin
        self._depth = frame.depth
        self._log_step(element, "failure")
        self._depth -= 1

    def _get_frame_from_depth(self):
        for i in xrange(len(self._stack)-1, -1, -1):
            frame = self._stack[i]
            if frame.depth == self._depth:
                return frame
        return None

    def _get_frame_from_actor(self, actor):
        for i in xrange(len(self._stack)-1, -1, -1):
            frame = self._stack[i]
            if frame.actor is actor:
                return frame
        return None

    def _log_step(self, parser, message):
        if not self._log: return
        indent = "   " * self._depth
        output = "%s%s: %s" % (indent, message, parser)
        self._log.debug(output)
        if self._index != self._previous_index:
            self._previous_index = self._index
            output = "%s -- Decoding State: '%s'" % (indent, str(self))
            self._log.debug(output)


#---------------------------------------------------------------------------

class Node(object):

    __slots__ = ("parent", "children", "actor",
                    "data", "begin", "end", "depth")

    def __init__(self, parent, actor, data, begin, end, depth):
        self.parent = parent; self.actor = actor; self.data = data
        self.begin = begin; self.end = end; self.depth = depth
        self.children = []

    def __str__(self):
        return "Node: %s, %s" % (self.actor, self.words())

    def add_child(self, child):
        self.children.append(child)

    def match(self):
        return self.data[self.begin : self.end]

    def value(self):
        return self.actor.value(self)

    def pretty_string(self, indent = ""):
        if not self.children:
            return "%s%s" % (indent, str(self))
        else:
            return "%s%s\n" % (indent, str(self)) \
                + "\n".join([n  .pretty_string(indent + "  ") \
                    for n in self.children])


#---------------------------------------------------------------------------
# Element base class.

class ParserElementBase(object):

    def __init__(self, name=None):
        self._name = name

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def _str(self, argument):
        if self._name:
            return "%s(%s)" % (self._name, argument)
        else:
            return "%s(%s)" % (self.__class__.__name__, argument)

    def __str__(self):
        return self._str("...")

    name = property(lambda self: self._name,
                        doc="Read-only access to name attribute.")

    def _get_children(self):
        return ()
    children = property(lambda self: self._get_children(),
                        doc="Generalized access to child elements.")

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def parse(self, state):
        raise NotImplementedError("Call to virtual method parse()"
                                  " in class %s" % self)

    def value(self, node):
        return node.match()


#---------------------------------------------------------------------------
# Basic structural element classes.

class Sequence(ParserElementBase):

    def __init__(self, children=(), name=None):
        ParserElementBase.__init__(self, name)
        self._children = children

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        return self._str("%d children" % len(self._children))

    def _get_children(self):
        return self._children

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def parse(self, state):
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
        path = [self._children[0].parse(state)]
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
                    path.append(self._children[len(path)].parse(state))
                else:
                    # Sequence complete, all children decoded successfully.
                    state.decode_success(self)
                    yield state
                    state.decode_retry(self)

        # Sequence of children could not all decode successfully: failure.
        state.decode_failure(self)
        return

    def value(self, node):
        return [c.value() for c in node.children]


#---------------------------------------------------------------------------

class Repetition(ParserElementBase):

    def __init__(self, child, min=1, max=None, name=None):
        ParserElementBase.__init__(self, name)

        if not isinstance(child, ParserElementBase):
            raise TypeError("Child %s must be a"
                            " ParserElementBase instance." % child)
        self._child = child
        self._min = min
        self._max = max
        self._greedy = True

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        return self._str("")

    def _get_children(self):
        return (self._child, )

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def parse(self, state):
        state.decode_attempt(self)

        # Attempt to walk a path through the entire sequence of children
        #  so that each one decodes successfully.
        path = [self._child.parse(state)]
        while path:
            # Allow the last child to attempt decoding.
            try: path[-1].next()
            except StopIteration:
                # Last child failed to decode, remove from path to
                #  allow the one-before-last child to reattempt.
                path.pop()

                if self._greedy and len(path) >= self._min:
                    # Path long enough, yield success.
                    state.decode_success(self)
                    yield state
                    state.decode_retry(self)

            else:
                # Last child successfully decoded.
                if not self._max or len(path) < self._max:
                    if not self._greedy and len(path) >= self._min:
                        # Path long enough, yield success.
                        state.decode_success(self)
                        yield state
                        state.decode_retry(self)
                    # Path not too long, append the next child.
                    path.append(self._child.parse(state))
                else:
                    # Path length at maximum, yield success.
                    state.decode_success(self)
                    yield state
                    state.decode_retry(self)

        # Sequence of children could not all decode successfully: failure.
        state.decode_failure(self)
        return

    def value(self, node):
        return [c.value() for c in node.children]


#---------------------------------------------------------------------------

class Alternative(ParserElementBase):

    def __init__(self, children=(), name=None):
        ParserElementBase.__init__(self, name)
        self._children = children

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        return self._str("%d children" % len(self._children))

    def _get_children(self):
        return self._children

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def parse(self, state):
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
            for result in child.parse(state):
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
        return node.children[0].value()


#---------------------------------------------------------------------------

class Optional(ParserElementBase):

    def __init__(self, child, greedy=True, name=None):
        ParserElementBase.__init__(self, name)

        if not isinstance(child, ParserElementBase):
            raise TypeError("Child %s must be a"
                            " ParserElementBase instance." % child)
        self._child = child
        self._greedy = greedy

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        return self._str("")

    def _get_children(self):
        return (self._child, )

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def parse(self, state):
        state.decode_attempt(self)

        # If in greedy mode, allow the child to decode before.
        if self._greedy:
            for result in self._child.parse(state):
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
            # Rollback decoding after null-decode.  Perhaps not absolutely
            #  necessary, but should be done for good form.
            state.decode_rollback(self)

            for result in self._child.parse(state):
                state.decode_success(self)
                yield state
                state.decode_retry(self)

        # No more decoding possibilities available, failure.
        state.decode_failure(self)
        return

    def value(self, node):
        if node.children:
            return node.children[0].value()
        else:
            return None


#---------------------------------------------------------------------------
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------

class String(ParserElementBase):

    def __init__(self, string, name=None):
        ParserElementBase.__init__(self, name)
        self._string = string

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        return self._str("%s" % self._string)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def parse(self, state):
        state.decode_attempt(self)

        # Check if the next characters match the target string.
        if state.next(len(self._string)) == self._string:
            state.decode_success(self)
            yield state
            state.decode_retry(self)

        state.decode_failure(self)
        return


#---------------------------------------------------------------------------

class CharacterSeries(ParserElementBase):

    def __init__(self, set, optional=False, exclude=False, name=None):
        ParserElementBase.__init__(self, name)
        self._set = set
        self._optional = optional
        self._exclude = exclude

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        return self._str("%s" % self._set)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def parse(self, state):
        state.decode_attempt(self)

        # Gobble as many valid characters as possible.
        count = 0
        if self._exclude:
            while not state.finished() and state.peek(1) not in self._set:
                state.next(1)
                count += 1
        else:
            while not state.finished() and state.peek(1) in self._set:
                state.next(1)
                count += 1

        if self._optional or count > 0:
            state.decode_success(self)
            yield state
            state.decode_retry(self)

        state.decode_failure(self)
        return


#---------------------------------------------------------------------------

class Whitespace(CharacterSeries):

    def __init__(self, optional=False, name=None):
        set = string.whitespace
        CharacterSeries.__init__(self, set, optional=optional, name=name)

    def __str__(self):
        return self._str("")


class Letters(CharacterSeries):

    def __init__(self, name=None):
        set = string.letters
        CharacterSeries.__init__(self, set, name=name)

    def __str__(self):
        return self._str("")


class Alphanumerics(CharacterSeries):

    def __init__(self, name=None):
        set = string.letters + string.digits
        CharacterSeries.__init__(self, set, name=name)

    def __str__(self):
        return self._str("")



def print_matches(node, indent = ""):
    if not indent: print "Nodes:"
    print indent, "%s: %r %s" % (node.parser.__class__.__name__, node.match(), id(node.parent))
    [print_matches(c, indent + "   ") for c in node.children]
def print_values(node, indent = ""):
    if not indent: print "Values:"
    print indent, "%s: %r %s" % (node.parser.__class__.__name__, node.value(), id(node.parent))
    [print_values(c, indent + "   ") for c in node.children]

