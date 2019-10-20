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
Input stream parsing framework
============================================================================

Dragonfly's generic input stream parser is built around the concept of
parser elements, each of which can consume a certain form of input.  These
parser elements can be constructed into a hierarchy describing the expected
type of input they are meant to process.

"""


#---------------------------------------------------------------------------

import string
import re
import locale
import logging

from six import string_types, text_type, binary_type


class ParserError(Exception):
    pass


#---------------------------------------------------------------------------

class Parser(object):

    def __init__(self, parser_element, log=None):
        self._parser_element = parser_element
        self._log = log

    def parse(self, input, must_finish=True):
        state = State(input, log=self._log)
        generator = self._parser_element.parse(state)
        for _ in generator:
            if not must_finish or state.finished():
                # Parse complete, return result.
                node = state.build_parse_tree()
                return node.value()
        # Failed to parse.
        return None

    def parse_node(self, input, must_finish=True):
        state = State(input, log=self._log)
        generator = self._parser_element.parse(state)
        for result in generator:
            if not must_finish or state.finished():
                # Parse complete, return result.
                node = state.build_parse_tree()
                return node
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
        self._log_debug = self._log.isEnabledFor(logging.DEBUG) if self._log else False
        self._stack = []
        self._depth = 0
        self._previous_index = None

    def initialize_decoding(self):
        self._depth = 0
        self._stack = []
        self._previous_index = None

    def __repr__(self):
        return self.position_string()

    #-----------------------------------------------------------------------
    # Methods for accessing recognition content.

    def position_string(self, width=20, width_before=6):
        mark, continuation = ">>", "."
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
                    frame.begin, frame.end, frame.depth,
                    frame.value)
        if parent:
            parent.add_child(node)
        index += 1
        while index < len(self._stack):
            if self._stack[index].depth != frame.depth + 1:
                break
            child, index = self._build_parse_node(index, node)
        return node, index

    #-----------------------------------------------------------------------
    # Methods for tracking parsing of input.

    class _Frame(object):
        __slots__ = ("depth", "actor", "begin", "end", "value")

        def __init__(self, depth, actor, begin):
            self.depth, self.actor, self.begin = depth, actor, begin
            self.value, self.end = None, None

    def decode_attempt(self, element):
        # assert isinstance(element, ParserElementBase)
        self._depth += 1
        self._stack.append(State._Frame(self._depth, element, self._index))
        if self._log_debug:
            self._log_step(element, "attempt")

    def decode_retry(self, element):
        # assert isinstance(element, ParserElementBase)
        frame = self._get_frame_from_actor(element)
        self._depth = frame.depth
        if self._log_debug:
            self._log_step(element, "retry")

    def decode_rollback(self, element):
        # assert isinstance(element, ParserElementBase)
        frame = self._get_frame_from_depth()
        if not frame or frame.actor != element:
            raise ParserError("Parser decoding stack broken")
        if frame is self._stack[-1]:
            # Last parser on the stack, rollback.
            self._index = frame.begin
        else:
            raise ParserError("Parser decoding stack broken")
        if self._log_debug:
            self._log_step(element, "rollback")

    def decode_success(self, element, value=None):
        # assert isinstance(element, ParserElementBase)
        if self._log_debug:
            self._log_step(element, "success")
        frame = self._get_frame_from_depth()
        if not frame or frame.actor != element:
            raise ParserError("Parser decoding stack broken.")
        frame.end = self._index
        frame.value = value
        self._depth -= 1

    def decode_failure(self, element):
        # assert isinstance(element, ParserElementBase)
        frame = self._stack.pop()
        self._index = frame.begin
        self._depth = frame.depth
        if self._log_debug:
            self._log_step(element, "failure")
        self._depth -= 1

    def _get_frame_from_depth(self):
        for frame in reversed(self._stack):
            if frame.depth == self._depth:
                return frame
        return None

    def _get_frame_from_actor(self, actor):
        for frame in reversed(self._stack):
            if frame.actor is actor:
                return frame
        return None

    def _log_step(self, parser, message):
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
                 "data", "begin", "end", "depth", "success_value")

    def __init__(self, parent, actor, data, begin, end, depth, value):
        self.parent, self.actor, self.data = parent, actor, data
        self.begin, self.end, self.depth = begin, end, depth
        self.success_value = value
        self.children = []

    def __repr__(self):
        if isinstance(self.data, binary_type):
            data = self.data.decode(locale.getpreferredencoding())
        else:
            data = text_type(self.data)
        return "Node: %s, %s" % (self.actor, data)

    def add_child(self, child):
        self.children.append(child)

    def match(self):
        return self.data[self.begin : self.end]

    def value(self):
        if self.success_value is not None:
            return self.success_value
        else:
            return self.actor.value(self)

    def get_children(self, name=None, actor_type=None, shallow=True):
        found = []
        for child in self.children:
            if (    (not name or child.actor.name == name)
                and (not actor_type or isinstance(child.actor, actor_type))):
                found.append(child)
            if shallow and child.actor.name:
                continue
            found.extend(child.get_children(name=name, actor_type=actor_type,
                                            shallow=shallow))
        return found

    def get_child(self, name=None, actor_type=None, shallow=True):
        for child in self.children:
            if (    (not name or child.actor.name == name)
                and (not actor_type or isinstance(child.actor, actor_type))):
                return child
            if shallow and child.actor.name:
                continue
            result = child.get_child(name=name, actor_type=actor_type,
                                     shallow=shallow)
            if result:
                return result
        return None

    def pretty_string(self, indent=""):
        if not self.children:
            return "%s%s" % (indent, str(self))
        else:
            return ("%s%s\n" % (indent, str(self)) +
                    "\n".join([n  .pretty_string(indent + "  ")
                               for n in self.children]))


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

    def __repr__(self):
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

    def __repr__(self):
        return self._str("%d children" % len(self._children))

    def _get_children(self):
        return self._children

    @property
    def child_list(self):
        return self._children

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def parse(self, state):
        state.decode_attempt(self)

        # Special case for an empty sequence.
        if not self._children:
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
            try:
                next(path[-1])
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

    def __repr__(self):
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
            try:
                next(path[-1])
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
        self._children = list(children)

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __repr__(self):
        return self._str("%d children" % len(self._children))

    def _get_children(self):
        return tuple(self._children)

    @property
    def child_list(self):
        return self._children

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def parse(self, state):
        state.decode_attempt(self)

        # Special case for an empty list of alternatives.
        if not self._children:
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

    def __repr__(self):
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


#===========================================================================

class String(ParserElementBase):
    r"""
        Parser element for static strings.

        Usage examples:
        >>> def parse_multiple(element, input):
        ...     parser = Parser(element)
        ...     return parser.parse_multiple(input, must_finish=False)
        >>> parse_multiple(String("foo"), "foo")
        ['foo']
        >>> parse_multiple(String("foo"), "foobar")
        ['foo']
        >>> parse_multiple(String("\n\t "), "\n\t foo")
        ['\n\t ']
        >>> parse_multiple(String("foo"), "bar")
        []
        >>> parse_multiple(String("foo"), " foo")
        []

    """

    def __init__(self, string, name=None):
        ParserElementBase.__init__(self, name)
        self._string = string

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __repr__(self):
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
    """
    Class for parsing from a character series or pattern.
    """

    def __init__(self, set, optional=False, exclude=False, name=None,
                 pattern=None):
        ParserElementBase.__init__(self, name)
        self._set = set
        self._optional = optional
        self._exclude = exclude
        self._pattern = pattern

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __repr__(self):
        return self._str("%s" % self._set)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def char_matches(self, c):
        if self._set:
            return c in self._set
        elif self._pattern:
            return bool(self._pattern.match(c))
        else:
            return False

    def parse(self, state):
        state.decode_attempt(self)

        # Gobble as many valid characters as possible.
        count = 0
        if self._exclude:
            while (not state.finished() and not
                    self.char_matches(state.peek(1))):
                state.next(1)
                count += 1
        else:
            while (not state.finished() and
                    self.char_matches(state.peek(1))):
                state.next(1)
                count += 1

        if self._optional or count > 0:
            state.decode_success(self)
            yield state
            state.decode_retry(self)

        state.decode_failure(self)
        return


#---------------------------------------------------------------------------

class Choice(Alternative):

    def __init__(self, choices, name=None):
        choice_pairs = []
        choice_elements = []
        for key, value in choices.items():
            if isinstance(key, string_types):
                element = String(key)
            elif isinstance(key, ParserElementBase):
                element = key
            else:
                raise TypeError("Invalid choice key: %r" % key)
            choice_pairs.append((element, value))
            choice_elements.append(element)
        self._choice_pairs = choice_pairs
        Alternative.__init__(self, choice_elements, name)

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __repr__(self):
        return self._str("%d choices" % len(self._choice_pairs))

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def value(self, node):
        actor = node.children[0].actor
        for element, value in self._choice_pairs:
            if actor == element:
                return value
        raise ParserError("Invalid child element: %s" % actor)


#---------------------------------------------------------------------------

class Whitespace(CharacterSeries):

    def __init__(self, optional=False, name=None):
        set = string.whitespace
        CharacterSeries.__init__(self, set, optional=optional, name=name)

    def __repr__(self):
        return self._str("")


class Letters(CharacterSeries):
    """
    Class for parsing ascii and non-ascii letter characters.
    """
    def __init__(self, name=None):
        pattern = re.compile(r"\w", re.UNICODE)
        CharacterSeries.__init__(self, None, name=name, pattern=pattern)

    def __repr__(self):
        return self._str("")

    def char_matches(self, c):
        if c.isdigit():
            return False
        else:
            return super(Letters, self).char_matches(c)


class Alphanumerics(CharacterSeries):
    """
    Class for parsing ascii and non-ascii letter and digit characters.
    """
    def __init__(self, name=None):
        pattern = re.compile(r"\w", re.UNICODE)
        CharacterSeries.__init__(self, None, name=name, pattern=pattern)

    def __repr__(self):
        return self._str("")


#---------------------------------------------------------------------------

class QuotedStringContent(ParserElementBase):

    escape_char    = "\\"
    valid_chars    = string.printable
    escaped_chars  = {
                      "n":  "\n",
                      "t":  "\t",
                     }
    valid_char_pattern = re.compile(r"\w", re.UNICODE)

    def __init__(self, delimiter_string, name=None):
        self.delimiter_string = delimiter_string
        ParserElementBase.__init__(self, name)

    def valid_char(self, c):
        """
        Check whether a character is a valid. Valid characters include all
        Unicode alphanumeric characters and any characters in
        self.valid_chars.
        :type c: str
        :rtype: bool
        """
        if c in self.valid_chars:
            return True
        else:
            return bool(self.valid_char_pattern.match(c))

    def parse(self, state):
        state.decode_attempt(self)

        # Gobble as many valid characters as possible.
        characters = []
        while not state.finished():
            next_char = state.peek(1)

            # If next_char escapes, look forward past it and
            #  handle the escaped character.
            if next_char == self.escape_char:
                # If there's nothing after the escaped char, then
                #  we can't gobble the escape character itself.
                #  So we're done.
                if state.remaining() < 2:
                    break
                escaped_char = state.peek(2)[1]
                if escaped_char in self.escaped_chars:
                    # The escaped character has a special transformation.
                    next_char = self.escaped_chars[escaped_char]
                else:
                    # The escaped character is not special,
                    #  so simply unescape it.
                    next_char = escaped_char
                    if not self.valid_char(next_char):
                        break
                state.next(1)  # Gobble self.escape_char.

            # If self.delimiter_string is next, then we're done.
            elif state.peek(len(self.delimiter_string)) == self.delimiter_string:
                break

            # If next_char is not acceptable, don't gobble it.
            elif not self.valid_char(next_char):
                break

            state.next(1)  # Gobble next_char.
            characters.append(next_char)

        value = "".join(characters)
        state.decode_success(self, value)
        yield state
        state.decode_retry(self)
        state.decode_failure(self)
        return


#---------------------------------------------------------------------------

class QuotedString(Alternative):
    """
        Parser element for quoted strings.

        Simple usage showing default delimiters:
        >>> parser = Parser(QuotedString())
        >>> parser.parse("''")
        ''
        >>> parser.parse("'Hello world!'")
        'Hello world!'
        >>> parser.parse('"Hello world!"')
        'Hello world!'

        Special characters within the quoted string can be escaped.
        >>> parser.parse(r'"Hello \"world\"!"')  #doctest: +SKIP
        Note back to get these escaping examples to run using doctest
        they must include double escapes, which are obviously not required
        in actual code.
        >>> parser.parse(r'"Hello \\"world\\"!"')
        'Hello "world"!'
        >>> print(parser.parse(r'"Hello \\\\ \\"world\\"!\\nGoodbye \\'universe\\'..."'))
        Hello \ "world"!
        Goodbye 'universe'...

        This element supports asymmetric open-close delimiters:
        >>> parser = Parser(QuotedString([("[[", "]]")]))
        >>> parser.parse("[[Hello world!]]")
        'Hello world!'
        >>> parser.parse("[[Hello world!]] Goodbye.", must_finish=False)
        'Hello world!'

    """

    # Open-close delimiter pairs.
    default_delimiters = (
                          ('"', '"'),
                          ("'", "'"),
                         )

    def __init__(self, delimiters=default_delimiters, name=None):
        self.delimiters = delimiters
        children = []
        for open_delimiter, close_delimiter in self.delimiters:
            delimiter_children = (
                                  String(open_delimiter),
                                  QuotedStringContent(close_delimiter),
                                  String(close_delimiter),
                                 )
            child = Sequence(delimiter_children)
            children.append(child)
        Alternative.__init__(self, children, name=name)

    def value(self, node):
        return node.children[0].children[1].value()


#---------------------------------------------------------------------------

class UnsignedInteger(CharacterSeries):
    """
        Parser element for unsigned integer literals.

        Simple usage examples:
        >>> from dragonfly.parser import Parser
        >>> parser = Parser(UnsignedInteger())
        >>> parser.parse("0")
        0
        >>> parser.parse("1234")
        1234
        >>> parser.parse("0001234")
        1234

    """

    digits_set = string.digits

    def __init__(self, name=None):
        CharacterSeries.__init__(self, self.digits_set, name)

    def value(self, node):
        return int(CharacterSeries.value(self, node))


#---------------------------------------------------------------------------

class Integer(Sequence):
    """
        Parser element for quoted strings.

        Simple usage examples:
        >>> from dragonfly.parser import Parser
        >>> parser = Parser(Integer())
        >>> parser.parse("0")
        0
        >>> parser.parse("+0")
        0
        >>> parser.parse("-000")
        0
        >>> parser.parse("1234")
        1234
        >>> parser.parse("+001234")
        1234
        >>> parser.parse("-001234")
        -1234

    """

    sign_strings = {
                    "+":  1,
                    "-": -1,
                   }
    digits_set = UnsignedInteger.digits_set

    def __init__(self, name=None):
        children = (
                    Optional(Choice(self.sign_strings)),
                    UnsignedInteger(),
                   )
        Sequence.__init__(self, children, name)

    def value(self, node):
        sign = node.children[0].value() or 1
        magnitude = node.children[1].value()
        return sign * magnitude


#---------------------------------------------------------------------------

class Float(Sequence):
    """
        Parser element for decimal fraction literals.

        Usage examples:
        >>> from dragonfly.parser import Parser
        >>> parser = Parser(Float())
        >>> parser.parse("0.0")
        0.0
        >>> parser.parse(".000")
        0.0
        >>> parser.parse("-.0")
        0.0
        >>> parser.parse("1.0")
        1.0
        >>> parser.parse("-1.0")
        -1.0
        >>> parser.parse("-1.75")
        -1.75

    """

    separator_string = "."

    def __init__(self, name=None):
        digits = CharacterSeries(set=string.digits)
        children = (
                    Optional(Alternative([
                                         Integer(),
                                         Choice(Integer.sign_strings, name="sign_only"),
                                        ])),
                    String(self.separator_string),
                    UnsignedInteger(),
                   )
        Sequence.__init__(self, children=children, name=name)

    def value(self, node):
        sign_only_node = node.get_child(name="sign_only")
        if sign_only_node:
            if float(sign_only_node.data) >= 0:
                integer_part = ""
            else:
                integer_part = "-"
        else:
            integer_part = node.children[0].value() or 0
        fractional_part = node.children[2].value()
        return float("%s.%d" % (integer_part, fractional_part))


#---------------------------------------------------------------------------

def print_matches(node, indent=""):
    if not indent:
        print("Nodes:")
    print(indent, "%s: %r %s" % (node.actor.__class__.__name__,
                                 node.match(), id(node.parent)))
    [print_matches(c, indent + "   ") for c in node.children]


def print_values(node, indent=""):
    if not indent:
        print("Values:")
    print(indent, "%s: %r %s" % (node.actor.__class__.__name__, node.value(),
                                 id(node.parent)))
    [print_values(c, indent + "   ") for c in node.children]
