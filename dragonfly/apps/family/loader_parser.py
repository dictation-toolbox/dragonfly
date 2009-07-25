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
Parser elements specific to the command family input forms
============================================================================

"""

import string
from ...parser import (Parser, ParserElementBase,
                       Sequence, Alternative, Repetition, Optional,
                       String, Choice, CharacterSeries, Whitespace,
                       QuotedString, UnsignedInteger, Integer, Float)


#---------------------------------------------------------------------------

class Identifier(object):

    def __init__(self, name):
        self.name = name    

    def __str__(self):
        return "Identifier(%r)" % self.name

    def __repr__(self):
        return "Identifier(%r)" % self.name

    def __ne__(self, other):
        return not (self == other)

    def __eq__(self, other):
        if isinstance(other, Identifier):
            return self.name == other.name
        else:
            return NotImplemented


class Argument(object):

    def __init__(self, name=None, value=None):
        self.name = name    
        self.value = value

    def __str__(self):
        return "Argument(%r, %r)" % (self.name, self.value)

    def __ne__(self, other):
        return not (self == other)

    def __eq__(self, other):
        if isinstance(other, Argument):
            return self.name == other.name and self.value == other.value
        else:
            return NotImplemented


class Call(object):

    def __init__(self, function, arguments):
        self.function = function
        self.arguments = arguments

    def __str__(self):
        argument_string = ", ".join(str(a) for a in self.arguments)
        return "Call(%r, %s)" % (self.function, argument_string)

    def __ne__(self, other):
        return not (self == other)

    def __eq__(self, other):
        if isinstance(other, Call):
            if self.function != other.function:
                return False
            if len(self.arguments) != len(other.arguments):
                return False
            for mine, theirs in zip(self.arguments, other.arguments):
                if mine != theirs:
                    return False
            return True
        else:
            return NotImplemented


#---------------------------------------------------------------------------

class IdentifierElement(CharacterSeries):
    """
        Parser element for identifiers.

        Usage examples:
        >>> from dragonfly.parser import Parser
        >>> parser = Parser(IdentifierElement())
        >>> def test_identifier_element(input):
        ...     output = parser.parse(input)
        ...     if not output: return False
        ...     assert isinstance(output, Identifier)
        ...     assert output.name == input
        ...     return True
        >>> assert test_identifier_element("foo_bar")
        >>> assert test_identifier_element("foo.bar")
        >>> assert test_identifier_element("foo.bar_baz")
        >>> assert not test_identifier_element("invalid/character")
        >>> assert not test_identifier_element("invalid character")

    """

    valid_chars = "".join((
                           string.uppercase,
                           string.lowercase,
                           string.digits,
                           "_.",
                         ))

    def __init__(self, name=None):
        CharacterSeries.__init__(self, set=self.valid_chars, name=name)

    def value(self, node):
        name = CharacterSeries.value(self, node)
        return Identifier(name)


class ValueElement(Alternative):
    """
        Parser element for values.

        Usage examples:
        >>> from dragonfly.parser import Parser
        >>> parser = Parser(ValueElement())
        >>> def test_value_element(input, identifier):
        ...     output = parser.parse(input)
        ...     if not output: return False
        ...     if identifier:
        ...         assert isinstance(output, Identifier)
        ...         assert output.name == input
        ...     else:
        ...         assert isinstance(output, basestring)
        ...         input = input.decode("string_escape")  # Interpret escaped chars.
        ...         assert output == input[1:-1]           # Strip off quotation marks.
        ...     return True
        >>> assert test_value_element("foo_bar", True)
        >>> assert test_value_element("foo.bar", True)
        >>> assert test_value_element("'foo_bar'", False)
        >>> assert test_value_element('"foo_bar"', False)
        >>> assert test_value_element(r'"Hello \\"world\\"!"', False)

    """

    def __init__(self, name=None):
        children = (
                    IdentifierElement(),
                    QuotedString(),
                   )
        Alternative.__init__(self, children, name=name)


class ArgumentElement(Sequence):
    """
        Parser element for call arguments.

        Usage examples:
        >>> from dragonfly.parser import Parser
        >>> parser = Parser(ArgumentElement())
        >>> def test_argument_element(input, name, value):
        ...     output = parser.parse(input)
        ...     if not output: return False
        ...     assert isinstance(output.name, basestring) or output.name is None
        ...     assert output.name == name
        ...     assert isinstance(output.value, (basestring, Identifier))
        ...     assert output.value == value
        ...     return True
        >>> assert test_argument_element("foo_bar",     None,     Identifier("foo_bar"))
        >>> assert test_argument_element('"foo"',       None,     "foo")
        >>> assert test_argument_element("foo=bar",     "foo",    Identifier("bar"))
        >>> assert test_argument_element("foo='bar'",   "foo",    "bar")
        >>> assert test_argument_element("foo ='bar'",  "foo",    "bar")
        >>> assert test_argument_element("foo= 'bar'",  "foo",    "bar")
        >>> assert test_argument_element("foo = 'bar'", "foo",    "bar")
        >>> assert test_argument_element("foo=\t'bar'", "foo",    "bar")
        >>> assert not test_argument_element("=foo",    None,     None)
        >>> assert not test_argument_element("foo=",    None,     None)
        >>> assert not test_argument_element("'foo'=bar", None,   None)

    """

    def __init__(self, name=None):
        ws = Optional(Whitespace())
        children = (
                    Optional(
                             Sequence([
                                       IdentifierElement(name="argid"), ws,
                                       String("="), ws,
                                     ])
                            ),
                    ValueElement(),
                   )
        Sequence.__init__(self, children, name=name)

    def value(self, node):
        name_node = node.get_child(name="argid",
                                   actor_type=IdentifierElement)
        if name_node:  name = name_node.value().name
        else:          name = None
        value = node.children[1].value()
        return Argument(name, value)


#---------------------------------------------------------------------------

class CallElement(Sequence):
    """
        Parser element for function call expressions.

        Usage examples:
        >>> from logging import getLogger
        >>> from dragonfly.parser import Parser
        >>> p = Parser(CallElement())
        >>> assert p.parse("foo()")           == Call("foo", [])
        >>> assert p.parse("foo(bar)")        == Call("foo", [Argument(value=Identifier("bar"))])
        >>> assert p.parse("foo(bar, baz)")   == Call("foo", [Argument(value=Identifier("bar")), \
                                                              Argument(value=Identifier("baz"))])
        >>> assert p.parse("foo(bar, 'baz')") == Call("foo", [Argument(value=Identifier("bar")), \
                                                              Argument(value="baz")])
        >>> assert p.parse("foo ( bar , \t'baz' )") == Call("foo", [Argument(value=Identifier("bar")), \
                                                                    Argument(value="baz")])

    """

    def __init__(self, name=None):
        ws = Optional(Whitespace())
        function = IdentifierElement(name="function")
        argument = ArgumentElement(name="arg")
        argument_list = Optional(Sequence([
                                  argument,
                                  Repetition(
                                             Sequence([
                                                       ws, String(","),
                                                       ws, argument,
                                                     ]),
                                             min=0,
                                             max=None,
                                            ),
                                ]))
        children = (
                    function,
                    ws,
                    String("("),
                    ws,
                    argument_list,
                    ws,
                    String(")"),
                   )
        Sequence.__init__(self, children, name)

    def value(self, node):
        function = node.get_child(name="function").value().name
        arguments = [n.value() for n in node.get_children(name="arg")]
        return Call(function, arguments)
