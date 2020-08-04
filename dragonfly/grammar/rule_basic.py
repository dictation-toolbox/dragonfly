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
BasicRule class
============================================================================

The BasicRule class is designed to make it easy to create a rule from an
element tree, rather than building one indirectly via compound element
specs.

This rule class has the following parameters to customize its behavior:

 - *name* (*str*) -- the rule's name
 - *element* (*Element*) -- root element for this rule
 - *exported* -- whether the rule is exported
 - *context* -- context in which the rule will be active

Each of these parameters can be passed as a (keyword) arguments to the
constructor, or defined as a class attribute in a derived class.

.. note::

   The BasicRule class has only limited support for the "extras" and
   "defaults" functionality of the
   :class:`dragonfly.grammar.rule_compound.CompoundRule` and
   :class:`dragonfly.grammar.rule_mapping.MappingRule` classes. By default,
   the *extras* dictionary passed to :meth:`_process_recognition` will
   only contain an entry for the root element of the rule.


Example usage
............................................................................

The BasicRule class can be used to define a voice-command as follows::

   from dragonfly import (BasicRule, Repetition, Alternative, Literal, Text,
                          Grammar)

   class ExampleRule(BasicRule):
       # Define a rule element that accepts 1 to 5 (exclusive) repetitions
       # of either 'test one', 'test two' or 'test three'. These commands
       # type their respective numbers in succession using the Text action.
       element = Repetition(
           Alternative((
               Literal("test one", value=Text("1")),
               Literal("test two", value=Text("2")),
               Literal("test three", value=Text("3")),
           )),
           1, 5
       )

   # Create a grammar with the example rule and load it.
   rule = ExampleRule()
   grammar = Grammar("BasicRule Example")
   grammar.add_rule(rule)
   grammar.load()


The above :class:`BasicRule` example can be defined without sub-classing::

   rule = BasicRule(
       element=Repetition(
           Alternative((
               Literal("test one", value=Text("1")),
               Literal("test two", value=Text("2")),
               Literal("test three", value=Text("3")),
           )),
           1, 5)
   )


Class reference
............................................................................

"""

from six import string_types

from .rule_base  import Rule
from .elements   import ElementBase
from ..actions.action_base import ActionBase


class BasicRule(Rule):
    """
        Rule class for implementing complete or partial voice-commands
        defined using an element.

        Constructor arguments:
         - *name* (*str*) -- the rule's name
         - *element* (*Element*) -- root element for this rule
         - *exported* (boolean) -- whether the rule is exported
         - *context* (*Context*) -- context in which the rule will be active

    """

    context = None
    _default_exported = True

    def __init__(self, name=None, element=None, exported=None,
                 context=None):
        if name    is None: name    = self.__class__.__name__
        if context is None: context = self.context

        # Complex handling of exported, because of clashing use of the
        #  exported name at the class level: property & class-value.
        if exported is not None:
            pass
        elif (hasattr(self.__class__, "exported")
              and not isinstance(self.__class__.exported, property)):
            exported = self.__class__.exported
        else:
            exported = self._default_exported

        # Similar complex handling of element.
        if element is not None:
            pass
        elif (hasattr(self.__class__, "element")
              and not isinstance(self.__class__.element, property)):
            element = self.__class__.element

        # Type checking of initialization values.
        assert isinstance(name, string_types)
        assert isinstance(element, ElementBase)

        self._name     = name

        Rule.__init__(self, self._name, element, exported=exported,
                      context=context)

    def value(self, node):
        node = node.children[0]
        value = node.value()

        if hasattr(value, "copy_bind"):
            # Prepare *extras* dict for passing to _copy_bind().
            extras = {
                "_grammar":            self.grammar,
                "_rule":               self,
                "_node":               node,
            }
            element = self._element
            name = element.name
            extra_node = node.get_child_by_name(name, shallow=True)
            if extra_node:
                extras[name] = extra_node.value()
            elif element.has_default():
                extras[name] = element.default

            value = value.copy_bind(extras)

        return value

    def process_recognition(self, node):
        """
            Process a recognition of this rule.

            This method is called by the containing Grammar when this
            rule is recognized.  This method collects information about
            the recognition and then calls *self._process_recognition*.

            - *node* -- The root node of the recognition parse tree.
        """
        # Prepare *extras* dict for passing to _process_recognition().
        extras = {
            "_grammar":  self.grammar,
            "_rule":     self,
            "_node":     node,
        }
        element = self._element
        name = element.name
        extra_node = node.get_child_by_name(name, shallow=True)
        if extra_node:
            extras[name] = extra_node.value()
        elif element.has_default():
            extras[name] = element.default

        # Call the method to do the actual processing.
        self._process_recognition(node, extras)

    def _process_recognition(self, node, extras):
        """
            Default recognition processing.

            This is the method which should be overridden in most cases
            to provide derived classes with custom recognition
            processing functionality.

            This default processing method executes actions if the node's
            value is an action or a list of actions.

            - *node* -- The root node of the recognition parse tree.
            - *extras* -- A dictionary of elements from the
              extras list contained within this recognition.
              Maps element name -> element value.

        """

        value = node.value()
        if isinstance(value, (list, tuple)):
            for item in node.value():
                if isinstance(item, ActionBase):
                    item.execute(extras)
        elif isinstance(value, ActionBase):
            value.execute(extras)
