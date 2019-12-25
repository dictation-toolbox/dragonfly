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
CompoundRule class
============================================================================

The CompoundRule class is designed to make it very easy to create a rule
based on a single compound spec.

This rule class has the following parameters to customize its behavior:

 - *spec* -- compound specification for the rule's root element
 - *extras* -- extras elements referenced from the compound spec
 - *defaults* -- default values for the extras
 - *exported* -- whether the rule is exported
 - *context* -- context in which the rule will be active

Each of these parameters can be passed as a (keyword) arguments to the
constructor, or defined as a class attribute in a derived class.


Example usage
............................................................................

The CompoundRule class can be used to define a voice-command as follows::

    class ExampleRule(CompoundRule):

        spec = "I want to eat <food>"
        extras = [Choice("food", {
                                  "(an | a juicy) apple": "good",
                                  "a [greasy] hamburger": "bad",
                                 }
                        )
                 ]

        def _process_recognition(self, node, extras):
            good_or_bad = extras["food"]
            print "That is a %s idea!" % good_or_bad

    rule = ExampleRule()
    grammar.add_rule(rule)


Class reference
............................................................................

"""
from six import string_types

from .rule_base  import Rule
from .elements   import ElementBase, Compound


#---------------------------------------------------------------------------

class CompoundRule(Rule):
    """
        Rule class based on the compound element.

        Constructor arguments:
         - *name* (*str*) -- the rule's name
         - *spec* (*str*) -- compound specification for the rule's
           root element
         - *extras* (sequence) -- extras elements referenced from the
           compound spec
         - *defaults* (*dict*) -- default values for the extras
         - *exported* (boolean) -- whether the rule is exported
         - *context* (*Context*) -- context in which the rule will be active

    """

    _name    = None
    spec     = None
    extras   = ()
    defaults = ()
    context  = None
    _default_exported = True

    #-----------------------------------------------------------------------

    def __init__(self, name=None, spec=None, extras=None,
                 defaults=None, exported=None, context=None):
        if name     is None: name     = self._name or self.__class__.__name__
        if spec     is None: spec     = self.spec
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

        assert isinstance(name, string_types)
        assert isinstance(spec, string_types)
        assert isinstance(extras, (list, tuple))
        for item in extras:
            assert isinstance(item, ElementBase)
        assert exported in (True, False)

        self._name     = name
        self._spec     = spec
        self.spec = spec
        self._extras   = dict((element.name, element) for element in extras)
        self._defaults = dict(defaults)

        child = Compound(spec, extras=self._extras)
        Rule.__init__(self, name, child, exported=exported, context=context)

    #-----------------------------------------------------------------------

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
        extras.update(self._defaults)
        for name, element in self._extras.items():
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

            This default processing method does nothing.

            - *node* -- The root node of the recognition parse tree.
            - *extras* -- A dictionary of all elements from the
              extras list contained within this recognition.
              Maps element name -> element value.
        """
