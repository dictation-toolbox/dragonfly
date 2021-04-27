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
Compound element classes
============================================================================

The following special *element* classes exist as convenient ways of
constructing basic element types from string specifications:

 * :class:`Compound` --
   a special element which parses a string spec to create a hierarchy of
   basic elements.

 * :class:`Choice` --
   a special element taking a :code:`choice` dictionary argument,
   interpreting keys as :class:`Compound` string specifications and values
   for what to return when compound specs are successfully decoded during
   the recognition process.

   The :code:`choice` argument may also be a list or tuple of strings, in
   which case the strings are also interpreted as :class:`Compound` strings
   specifications.  However, the values returned when compound specs are
   successfully decoded during the recognition process are the recognized
   words.  **Note**: these values will be matching part(s) of the compound
   specs.

"""

# pylint: disable=W0223
# Suppress abstract method warnings.

import locale
import logging
import re

from six import string_types, binary_type

from dragonfly.grammar.elements_basic import Alternative, ElementBase
from dragonfly.parsing.parse import spec_parser, CompoundTransformer, ParseError

#---------------------------------------------------------------------------
# The Compound class.

class Compound(Alternative):
    """
        Element which parses a string spec to create a hierarchy of basic
        elements.

        Constructor arguments:
         - *spec* (*str*) -- compound specification
         - *extras* (sequence) -- extras elements referenced from the
           compound spec
         - *actions* (*dict*) -- this argument is currently unused
         - *name* (*str*) -- the name of this element
         - *value* (*object*, default: *None*) --
           value to be returned when this element is successfully decoded
           If *None*, then the value(s) of child nodes are used instead
         - *value_func* (*callable*, default: *None*) --
           function to be called for the node value when this element is
           successfully decoded. If *None*, then the value(s) of child nodes
           are used. This argument takes precedence over the *value*
           argument if it is present
         - *elements* (sequence) -- same as the extras argument
         - *default* (default: *None*) -- the default value of this element

        Example:

        .. code:: python

           # Define a command to type the sum of two spoken integers between
           # 1 and 50 using a Compound element.
           mapping = {
               "type <XAndY>": Text("%(XAndY)d"),
           }
           extras = [
               Compound(
                   # Pass the compound spec and element name.
                   spec="<x> and <y>",
                   name="XAndY",

                   # Pass the internal IntegerRef extras.
                   extras=[IntegerRef("x", 1, 50), IntegerRef("y", 1, 50)],

                   # Pass a value function that adds the two spoken integers
                   # together.
                   value_func=lambda node, extras: extras["x"] + extras["y"])
           ]

    """

    _log = logging.getLogger("compound.parse")
    _parser = spec_parser

    def __init__(self, spec, extras=None, actions=None, name=None,
                 value=None, value_func=None, elements=None, default=None):
        # pylint: disable=too-many-arguments,too-many-branches
        if isinstance(spec, binary_type):
            spec = spec.decode(locale.getpreferredencoding())

        self._spec = spec
        self._value = value
        self._value_func = value_func

        if extras   is None:   extras   = {}
        if actions  is None:   actions  = {}
        if elements is None:   elements = {}

        # Convert extras argument from sequence to mapping.
        if isinstance(extras, (tuple, list)):
            mapping = {}
            for element in extras:
                if not isinstance(element, ElementBase):
                    self._log.error("Invalid extras item: %s", element)
                    raise TypeError("Invalid extras item: %s" % element)
                if not element.name:
                    self._log.error("Extras item does not have a name: %s", element)
                    raise TypeError("Extras item does not have a name: %s" % element)
                if element.name in mapping:
                    self._log.warning("Multiple extras items with the same name: %s", element)
                mapping[element.name] = element
            extras = mapping
        elif not isinstance(extras, dict):
            self._log.error("Invalid extras argument: %s", extras)
            raise TypeError("Invalid extras argument: %s" % extras)

        # Temporary transition code so that both "elements" and "extras"
        #  are supported as keyword arguments.
        if extras and elements:
            extras = dict(extras)
            extras.update(elements)
        elif elements:
            extras = elements
        self._extras = extras

        try:
            tree = self._parser.parse(spec)
        except Exception as e:
            self._log.error("Exception raised parsing %r: %s", spec, e)
            raise ParseError("Exception raised parsing %r: %s" % (spec, e))

        try:
            element = CompoundTransformer(self._extras).transform(tree)
        except Exception as e:
            self._log.error("Exception raised transforming %r: %s", spec, e)
            raise ParseError("Exception raised transforming %r: %s" % (spec, e))

        Alternative.__init__(self, (element,), name=name,
                             default=default)

    def __repr__(self):
        arguments = ["%r" % self._spec]
        if self.name:
            arguments.append("name=%r" % self.name)
        arguments = ", ".join(arguments)
        return "%s(%s)" % (self.__class__.__name__, arguments)

    def value(self, node):
        if self._value_func is not None:
            # Prepare *extras* dict for passing to value_func().
            extras = {"_node": node}
            for name, element in self._extras.items():
                extra_node = node.get_child_by_name(name, shallow=True)
                if extra_node:
                    extras[name] = extra_node.value()
                elif element.has_default():
                    extras[name] = element.default
            try:
                value = self._value_func(node, extras)
            except Exception as e:
                self._log.warning("Exception from value_func: %s", e)
                raise
            return value
        elif self._value is not None:
            return self._value
        else:
            return Alternative.value(self, node)


#---------------------------------------------------------------------------
# The Choice class which maps multiple Compound instances to values.

class Choice(Alternative):
    """
        Element allowing a dictionary of phrases (compound specs) to be
        recognized to be mapped to objects to be used in an action.

        A list or tuple of phrases to be recognized may also be used.  In
        this case the strings are also interpreted as :class:`Compound`
        string specifications.  However, the values returned when compound
        specs are successfully decoded during the recognition process are
        the recognized words.  **Note**: these values will be matching
        part(s) of the compound specs.

        Constructor arguments:
            - *name* (*str*) -- the name of this element
            - *choices* (*dict*, *list* or *tuple*) -- dictionary mapping
              recognized phrases to returned values **or** a list/tuple of
              recognized phrases
            - *extras* (*list*, default: *None*) -- a list of included
              extras
            - *default* (default: *None*) -- the default value of this
              element

        Example using a dictionary:

        .. code:: python

            # Tab switching command, e.g. 'third tab'.
            mapping = {
                "<nth> tab": Key("c-%(nth)s"),
            }
            extras = [
                Choice("nth", {
                    "first"         : "1",
                    "second"        : "2",
                    "third"         : "3",
                    "fourth"        : "4",
                    "fifth"         : "5",
                    "sixth"         : "6",
                    "seventh"       : "7",
                    "eighth"        : "8",
                    "(last | ninth)": "9",
                    "next"          : "pgdown",
                    "previous"      : "pgup",
                }),
            ]

        Example using a list:

        .. code:: python

            # Command for recognizing and typing nth words, e.g.
            # 'type third'.
            mapping = {
                "type <nth>": Text("%(nth)s"),
            }
            extras = [
                Choice("nth", [
                    "first",
                    "second",
                    "third",
                    "fourth",
                    "fifth",
                    "sixth",
                    "seventh",
                    "eighth",

                    # Note that the decoded value for a compound spec like
                    #  this one, when used in a list/tuple of choices,
                    #  rather than a dictionary, is the recognized word:
                    #  "last" or "ninth".
                    "(last | ninth)",

                    "next",
                    "previous",
                ]),
            ]
    """
    def __init__(self, name, choices, extras=None, default=None):
        # Argument type checking.
        assert isinstance(name, string_types) or name is None
        assert isinstance(choices, (dict, list, tuple))
        choices_is_sequence = isinstance(choices, (list, tuple))
        if choices_is_sequence:
            choices = {k: None for k in choices}

        for k, v in choices.items():
            assert isinstance(k, string_types)

        # Construct children from the given choice keys and values.
        self._choices = choices
        self._extras = extras
        children = []
        for k, v in choices.items():
            child = Compound(spec=k, value=v, extras=extras)
            children.append(child)

        # Initialize super class.
        Alternative.__init__(self, children=children,
                             name=name, default=default)
