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
    This file implements the MappingRule class.
"""


from dragonfly.grammar.rule     import Rule
from dragonfly.grammar.elements import ElementBase, Compound, Alternative
from dragonfly.actions.actions  import ActionBase


#---------------------------------------------------------------------------

class MappingRule(Rule):

    mapping  = {}
    extras   = []
    defaults = {}
    exported = True

    _key = "_MappingRule_item"

    #-----------------------------------------------------------------------

    def __init__(self, name=None, mapping=None, extras=None, defaults=None,
                 exported=None):
        if name     is None: name     = self.__class__.__name__
        if mapping  is None: mapping  = self.mapping
        if extras   is None: extras   = self.extras
        if defaults is None: defaults = self.defaults
        if exported is None: exported = self.exported

        # Type checking of initialization values.
        assert isinstance(name, (str, unicode))
        assert isinstance(mapping, dict)
        for key, value in mapping.iteritems():
            assert isinstance(key, (str, unicode))
        assert isinstance(extras, (list, tuple))
        for item in extras:
            assert isinstance(item, ElementBase)
        assert exported == True or exported == False

        self._name     = name
        self._mapping  = mapping
        self._extras   = dict([(element.name, element)
                     	       for element in extras])
        self._defaults = defaults

        children = []
        for spec, value in self._mapping.iteritems():
            c = Compound(spec, elements=self._extras,
                         name=self._key, value=value)
            children.append(c)

        element = Alternative(children)
        Rule.__init__(self, self._name, element, exported=exported)

    #-----------------------------------------------------------------------

    def process_recognition(self, node):
        """
            Process a recognition of this rule.

            This method is called by the containing Grammar when 
            this rule is recognized.  This method collects information
            about the recognition and then calls
            MappingRule._process_recognition.

            - *node* -- The root node of the recognition parse tree.
        """
        item_node = node.get_child_by_name(self._key)
        item_value = item_node.value()

        extras = self._defaults
        for name, element in self._extras.iteritems():
            extra_node = node.get_child_by_name(name)
            if not extra_node: continue
            extras[name] = extra_node.value()

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
                                   " cannot execute." % self)
