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


import dragonfly.parser as parser_
import dragonfly.actions.actionbase as actionbase_


class ActionStringError(Exception):
    pass


class _Argument(parser_.CharacterSeries):

    def __init__(self):
        import string
        characters = string.letters + string.digits + "-_/:"
        parser_.CharacterSeries.__init__(self, characters)


class _Element(parser_.Sequence):

    def __init__(self):
        argument_list = parser_.Optional(
            parser_.Sequence((
                parser_.Whitespace(optional=True),
                _Argument(),
                parser_.Whitespace(optional=True),
                parser_.Repetition(
                    parser_.Sequence((
                        parser_.String(","),
                        parser_.Whitespace(optional=True),
                        _Argument(),
                        parser_.Whitespace(optional=True),
                        )),
                    min=0),
                )),
            )
        elements = (
            parser_.Whitespace(optional=True),
            parser_.Alphanumerics(),
            parser_.Whitespace(optional=True),
            parser_.String("("),
            argument_list,
            parser_.String(")"),
            parser_.Whitespace(optional=True),
            )
        parser_.Sequence.__init__(self, elements)

    def value(self, node):
        name = node.children[1].value()

        optional = node.children[4]
        if not optional.children:
            arguments = ()
        else:
            sequence = optional.children[0]
            arguments = [sequence.children[1]]
            repetition = sequence.children[3]
            for sequence in repetition.children:
                arguments.append(sequence.children[2])
            arguments = [n.value() for n in arguments]

        return (name, arguments)


class _AcStrParserElement(parser_.Repetition):

    def __init__(self):
        element = _Element()
        parser_.Repetition.__init__(self, element)


class ActionString(actionbase_.ActionBase):

    _subtypes = {}

    def __init__(self, spec=None):
        actionbase_.ActionBase.__init__(self)
        self._parser = parser_.Parser(_AcStrParserElement())
        self.initialize(spec)

    def initialize(self, spec=None):
        self._spec = spec
        if spec is None: return

        # Parse the action string specification.
        result = self._parser.parse(spec)
        actions = [self._build_subtype(n, args) for (n, args) in result]
        [self.append(a) for a in actions]

    def _build_subtype(self, name, arguments):
        try: subtype = self._subtypes[name]
        except KeyError: raise ActionStringError(
                                        "Invalid subtype '%s'." % name)
        a = subtype()
        a.initialize(name, arguments)
        return a

    def i_register_subtype(cls, name, subtype):
        assert isinstance(name, str)
        assert issubclass(subtype, AcStrSubtype)
        cls._subtypes[name] = subtype
    i_register_subtype = classmethod(i_register_subtype)


class AcStrSubtype(actionbase_.ActionBase):

    _name = None

    def register(cls):
        assert isinstance(cls._name, str)
        ActionString.i_register_subtype(cls._name, cls)
    register = classmethod(register)

    def initialize(self, name, arguments):
        pass
