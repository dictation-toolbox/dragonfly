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
This file implements the CompoundRule class.

"""


from dragonfly.grammar.rule     import Rule
from dragonfly.grammar.elements import ElementBase, Compound


#---------------------------------------------------------------------------

class CompoundRule(Rule):

    _name    = None
    spec     = None
    extras   = []
    defaults = {}
    exported = True
    context  = None

    #-----------------------------------------------------------------------

    def __init__(self, name=None, spec=None, extras=None,
                 defaults=None, exported=None, context=None):
        if name     is None: name     = self._name or self.__class__.__name__
        if spec     is None: spec     = self.spec
        if extras   is None: extras   = self.extras
        if defaults is None: defaults = self.defaults
        if exported is None: exported = self.exported
        if context  is None: context  = self.context

        assert isinstance(name, (str, unicode))
        assert isinstance(spec, (str, unicode))
        assert isinstance(extras, (list, tuple))
        for item in extras:
            assert isinstance(item, ElementBase)
        assert exported == True or exported == False

        self._name     = name
        self._spec     = spec
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
        extras = dict(self._defaults)
        for name, element in self._extras.iteritems():
            extra_node = node.get_child_by_name(name, shallow=True)
            if not extra_node: continue
            extras[name] = extra_node.value()

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
        pass
