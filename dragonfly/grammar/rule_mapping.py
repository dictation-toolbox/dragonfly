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
MappingRule class
============================================================================

The MappingRule class is designed to make it very easy to create a rule
based on a mapping of spoken-forms to semantic values.

This class has the following parameters to customize its behavior:

 - *mapping* -- mapping of spoken-forms to semantic values
 - *extras* -- extras elements referenced from the compound spec
 - *defaults* -- default values for the extras
 - *exported* -- whether the rule is exported
 - *context* -- context in which the rule will be active

Each of these parameters can be passed as a (keyword) arguments to the
constructor, or defined as a class attribute in a derived class.


Example usage
............................................................................

The MappingRule class can be used to define a voice-command as follows::

    class ExampleRule(MappingRule):

        mapping  = {
                    "[feed] address [bar]":                Key("a-d"),
                    "subscribe [[to] [this] feed]":        Key("a-u"),
                    "paste [feed] address":                Key("a-d, c-v, enter"),
                    "feeds | feed (list | window | win)":  Key("a-d, tab:2, s-tab"),
                    "down [<n>] (feed | feeds)":           Key("a-d, tab:2, s-tab, down:%(n)d"),
                    "up [<n>] (feed | feeds)":             Key("a-d, tab:2, s-tab, up:%(n)d"),
                    "open [item]":                         Key("a-d, tab:2, c-s"),
                    "newer [<n>]":                         Key("a-d, tab:2, up:%(n)d"),
                    "older [<n>]":                         Key("a-d, tab:2, down:%(n)d"),
                    "mark all [as] read":                  Key("cs-r"),
                    "mark all [as] unread":                Key("cs-u"),
                    "search [bar]":                        Key("a-s"),
                    "search [for] <text>":                 Key("a-s") + Text("%(text)s\\n"),
                   }
        extras   = [
                    Integer("n", 1, 20),
                    Dictation("text"),
                   ]
        defaults = {
                    "n": 1,
                   }

    rule = ExampleRule()
    grammar.add_rule(rule)


Class reference
............................................................................

"""
from six import string_types

from .rule_base         import Rule
from .elements          import ElementBase, Compound, Alternative
from ..actions.actions  import ActionBase


#---------------------------------------------------------------------------

class MappingRule(Rule):
    """
        Rule class based on a mapping of spoken-forms to semantic values.

        Constructor arguments:
         - *name* (*str*) -- the rule's name
         - *mapping* (*dict*) -- mapping of spoken-forms to semantic
           values
         - *extras* (sequence) -- extras elements referenced from the
           spoken-forms in *mapping*
         - *defaults* (*dict*) -- default values for the extras
         - *exported* (boolean) -- whether the rule is exported
         - *context* (*Context*) -- context in which the rule will be active

    """

    mapping  = {}
    extras   = []
    defaults = {}
    context  = None
    _default_exported = True

    #-----------------------------------------------------------------------

    def __init__(self, name=None, mapping=None, extras=None, defaults=None,
                 exported=None, context=None):
        # pylint: disable=too-many-branches

        if name     is None: name     = self.__class__.__name__
        if mapping  is None: mapping  = self.mapping
        if extras   is None: extras   = self.extras
        if defaults is None: defaults = self.defaults
        if context  is None: context  = self.context

        # Complex handling of exported, because of clashing use of the
        #  exported name at the class level: property & class-value.
        if exported is not None:
            pass
        elif (hasattr(self.__class__, "exported")
              and not isinstance(self.__class__.exported, property)):
            exported = self.__class__.exported
        else:
            exported = self._default_exported

        # Type checking of initialization values.
        assert isinstance(name, string_types)
        assert isinstance(mapping, dict)
        for key, value in mapping.items():
            assert isinstance(key, string_types)
        assert isinstance(extras, (list, tuple))
        for item in extras:
            assert isinstance(item, ElementBase)
        assert exported in (True, False)

        self._name     = name
        self._mapping  = mapping
        self._extras   = {element.name : element for element in extras}
        self._defaults = defaults

        children = []
        for spec, value in self._mapping.items():
            c = Compound(spec, elements=self._extras, value=value)
            children.append(c)

        if children:  element = Alternative(children)
        else:         element = None
        Rule.__init__(self, self._name, element, exported=exported,
                      context=context)

    #-----------------------------------------------------------------------

    @property
    def specs(self):
        """
        Each spoken-form in the rule.
        :rtype: list
        """
        return [k for k, _ in self._mapping.items()]

    def value(self, node):
        node = node.children[0]
        value = node.value()

        if hasattr(value, "copy_bind"):
            # Prepare *extras* dict for passing to _copy_bind().
            extras = {
                "_grammar":  self.grammar,
                "_rule":     self,
                "_node":     node,
            }
            extras.update(self._defaults)
            for name, element in self._extras.items():
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

            This method is called by the containing Grammar when
            this rule is recognized.  This method collects information
            about the recognition and then calls
            MappingRule._process_recognition.

            - *node* -- The root node of the recognition parse tree.
        """
        item_value = node.value()

        # Prepare *extras* dict for passing to _process_recognition().
        extras = {
            "_grammar":  self.grammar,
            "_rule":     self,
            "_node":     node,
        }
        extras.update(self._defaults)
        for name, element in self._extras.items():
            extra_node = node.get_child_by_name(name, shallow=True)
            if extra_node:
                extras[name] = extra_node.value()
            elif element.has_default():
                extras[name] = element.default

        # Call the method to do the actual processing.
        self._process_recognition(item_value, extras)

    def _process_recognition(self, value, extras):
        """
            Default recognition processing.

            This is the method which should be overridden in most cases
            to provide derived classes with custom recognition
            processing functionality.

            This default processing method takes the mapping value
            from the recognition and, if it is an action, executes it
            with the given extras as a dynamic values.

            - *value* -- The mapping value recognized.
            - *extras* -- A dictionary of all elements from the
              extras list contained within this recognition.
              Maps element name -> element value.
        """
        if isinstance(value, ActionBase):
            value.execute(extras)
        elif self._log_proc:
            self._log_proc.warning("%s: mapping value is not an action,"
                                   " cannot execute.", self)
