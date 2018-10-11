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
        args = [str(a) for a in self.arguments]
        return "Call(f=%r, args=(%s))" % (self.function, ", ".join(args))

    def __repr__(self):
        return self.__str__()

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
        >>> from six import string_types
        >>> from dragonfly.parser import Parser
        >>> parser = Parser(ValueElement())
        >>> def test_value_element(input, identifier):
        ...     output = parser.parse(input)
        ...     if not output: return False
        ...     if identifier:
        ...         assert isinstance(output, Identifier)
        ...         assert output.name == input
        ...     else:
        ...         assert isinstance(output, string_types)
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
                    Integer(),
                    Float(),
                    QuotedString(),
                    IdentifierElement(),
                   )
        Alternative.__init__(self, children, name=name)


class ArgumentElement(Sequence):
    """
        Parser element for call arguments.

        Usage examples:
        >>> from six import string_types
        >>> from dragonfly.parser import Parser
        >>> parser = Parser(ArgumentElement())
        >>> def test_argument_element(input, name, value):
        ...     output = parser.parse(input)
        ...     if not output: return False
        ...     assert isinstance(output.name, string_types) or output.name is None
        ...     assert output.name == name
        ...     assert isinstance(output.value, (string_types, Identifier))
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


#---------------------------------------------------------------------------

class _ActionGroup(object):
    def __init__(self, items, factor=1):
        self.items = items
        self.factor = factor
    def build_tree(self):
        if len(self.items) == 1 and self.factor == 1:
            if isinstance(self.items[0], self.__class__):
                return self.items[0].build_tree()
            else:
                return self.items[0]
        branches = []
        for item in self.items:
            if isinstance(item, self.__class__):
                branch = item.build_tree()
                if isinstance(branch, tuple) and branch[1] == 1:
                    branches.extend(branch[0])
                else:
                    branches.append(branch)
            else:
                branches.append(item)
        return (branches, self.factor)

class ActionElement(Sequence):
    """
        Parser element for action expressions.

        Usage examples:
        >>> p = Parser(ActionElement())
        >>> from pprint import PrettyPrinter
        >>> pretty = lambda input: PrettyPrinter().pprint(p.parse(input))
        >>> pretty("foo()")
        Call(f='foo', args=())
        >>> pretty("(\t (foo()\t)* 1  )")
        Call(f='foo', args=())
        >>> pretty("foo() bar()")
        ([Call(f='foo', args=()), Call(f='bar', args=())], 1)
        >>> pretty("(foo()( bar())) baz()")
        ([Call(f='foo', args=()), Call(f='bar', args=()), Call(f='baz', args=())], 1)
        >>> pretty("foo() * 9 bar()")
        ([([Call(f='foo', args=())], 9), Call(f='bar', args=())], 1)
        >>> pretty("foo() * 'integer' bar()")
        ([([Call(f='foo', args=())], 'integer'), Call(f='bar', args=())], 1)
        >>> pretty("(foo() bar())*3 baz()")
        ([([Call(f='foo', args=()), Call(f='bar', args=())], 3),
          Call(f='baz', args=())],
         1)
        >>> pretty("((foo() bar())*3 (foo() bar())*'count')*7")
        ([([Call(f='foo', args=()), Call(f='bar', args=())], 3),
          ([Call(f='foo', args=()), Call(f='bar', args=())], 'count')],
         7)
        >>> pretty("(Key("") Key("")) * 7 Key("") * 3")
        ([([Call(f='Key', args=()), Call(f='Key', args=())], 7),
          ([Call(f='Key', args=())], 3)],
         1)

    """

    #-----------------------------------------------------------------------

    class MulExpression(Sequence):
        def __init__(self, unit_mul, ws):
            mul_factor = Alternative((
                                      UnsignedInteger(),
                                      QuotedString(),
                                    ))
            Sequence.__init__(self,
                              (
                               unit_mul,
                               Repetition(
                                          Sequence((
                                                    ws, String("*"),
                                                    ws, mul_factor,
                                                  )),
                                          min=1,
                                          #max=8,
                                         )
                             ))
        def value(self, node):
            unit_mul_value = node.children[0].value()
            factors = []
            for repetition in node.children[1].value():
                factors.append(repetition[3])
            result = unit_mul_value
            for f in factors:
                result = _ActionGroup([result], f)
            return result

    class AddExpression(Sequence):
        def __init__(self, unit_add, ws):
            Sequence.__init__(self,
                              (
                               unit_add,
                               Repetition(
                                          Sequence((
                                                    ws, unit_add,
                                                  )),
                                          min=0,
                                          #max=8,
                                         )
                             ))
        def value(self, node):
            unit_add_values = [node.children[0].value()]
            for repetition in node.children[1].value():
                unit_add_values.append(repetition[1])
            return _ActionGroup(unit_add_values)

    class GrpExpression(Sequence):
        def __init__(self, expr_add, ws):
            Sequence.__init__(self,
                              (
                               String("("),
                               ws, expr_add,
                               ws, String(")"),
                             ))
        def value(self, node):
            expr_add_value = node.children[2].value()
            return _ActionGroup([expr_add_value])

    single_call = CallElement()
    ws = Optional(Whitespace())
    unit_add = Alternative()
    unit_mul = Alternative()
    expr_mul = MulExpression(unit_mul, ws)
    expr_add = AddExpression(unit_add, ws)
    expr_grp = GrpExpression(expr_add, ws)
    unit_add.child_list.extend((single_call, expr_grp, expr_mul))
    unit_mul.child_list.extend((single_call, expr_grp))

    #-----------------------------------------------------------------------

    def __init__(self, name=None):
        children = (
                    self.expr_add,
                   )
        Sequence.__init__(self, children, name)

    def value(self, node):
        group = node.children[0].value()
        tree = group.build_tree()
        return tree


#---------------------------------------------------------------------------

class _ContextGroup(object):
    def __init__(self, operator, before, after=None):
        self.operator  = operator
        self.before    = before
        self.after     = after
    def build_tree(self):
        if isinstance(self.before, self.__class__):
            before = self.before.build_tree()
        else:
            before = self.before
        if self.after:
            if isinstance(self.after, self.__class__):
                after = self.after.build_tree()
            else:
                after = self.after
            return (self.operator, after, before)
        else:
            return (self.operator, before)

class ContextElement(Sequence):
    """
        Parser element for context expressions.

        Usage examples:
        >>> p = Parser(ContextElement())
        >>> from pprint import PrettyPrinter
        >>> pretty = lambda input: PrettyPrinter().pprint(p.parse(input))
        >>> pretty("foo()")
        Call(f='foo', args=())
        >>> pretty("foo() & bar()")
        ('&', Call(f='foo', args=()), Call(f='bar', args=()))
        >>> pretty("foo() & bar() | baz()")
        ('|',
         ('&', Call(f='foo', args=()), Call(f='bar', args=())),
         Call(f='baz', args=()))
        >>> pretty("foo() & (bar() | baz())")
        ('&',
         Call(f='foo', args=()),
         ('|', Call(f='bar', args=()), Call(f='baz', args=())))
        >>> pretty("!foo()")
        ('!', Call(f='foo', args=()))
        >>> pretty("foo() | !bar()")
        ('|', Call(f='foo', args=()), ('!', Call(f='bar', args=())))
        >>> pretty("!foo() & !(bar() | baz())")
        ('&',
         ('!', Call(f='foo', args=())),
         ('!', ('|', Call(f='bar', args=()), Call(f='baz', args=()))))

    """

    #-----------------------------------------------------------------------

    class SeriesExpression(Sequence):
        def __init__(self, unit, operator, ws):
            Sequence.__init__(self,
                              (
                               unit,
                               Repetition(
                                          Sequence((
                                                    ws, operator,
                                                    ws, unit,
                                                  )),
                                          min=0,
                                         )
                             ))
        def value(self, node):
            values = [node.children[0].value()]
            for repetition in node.children[1].value():
                operator_value  = repetition[1]
                unit_value      = repetition[3]
                values.extend((operator_value, unit_value))
            if len(values) == 1:
                return values[0]
            values.reverse()
            after     = values.pop()
            operator  = values.pop()
            before    = values.pop()
            group = _ContextGroup(operator, before, after)
            while values:
                operator  = values.pop()
                before    = values.pop()
                group     = _ContextGroup(operator, before, group)
            return group

    class NotExpression(Sequence):
        def __init__(self, unit_not, ws):
            Sequence.__init__(self, (String("!"), ws, unit_not))
        def value(self, node):
            operator  = node.children[0].value()
            value     = node.children[2].value()
            group     = _ContextGroup(operator, value)
            return group

    class GrpExpression(Sequence):
        def __init__(self, expr_series, ws):
            Sequence.__init__(self,
                              (
                               String("("),
                               ws, expr_series,
                               ws, String(")"),
                             ))
        def value(self, node):
            series_value = node.children[2].value()
            return series_value

    single_call  = CallElement()
    ws           = Optional(Whitespace())
    operator     = Alternative((String("&"), String("|")))
    unit_series  = Alternative()
    unit_not     = Alternative()
    expr_series  = SeriesExpression(unit_series, operator, ws)
    expr_grp     = GrpExpression(expr_series, ws)
    expr_not     = NotExpression(unit_not, ws)
    unit_not.child_list.extend((single_call, expr_grp))
    unit_series.child_list.extend((single_call, expr_not, expr_grp))

    #-----------------------------------------------------------------------

    def __init__(self, name=None):
        children = (
                    self.expr_series,
                   )
        Sequence.__init__(self, children, name)

    def value(self, node):
        root = node.children[0].value()
        if isinstance(root, _ContextGroup):
            tree = root.build_tree()
        else:
            tree = root
        return tree
