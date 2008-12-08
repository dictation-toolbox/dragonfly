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
    This file implements the Rule class, in grammar object which
    represents one natlink rule within a grammar.
"""


import types
import dragonfly.log as log_


class Rule(object):

    _log_load = log_.get_log("grammar.load")
    _log_eval = log_.get_log("grammar.eval")
    _log_proc = log_.get_log("grammar.process")
    _log      = log_.get_log("rule")
    _log_begin = log_.get_log("rule")

    def __init__(self, name, element, context=None,
                    imported=False, exported=False):
        self._name = name
        self._element = element
        self._imported = imported
        self._exported = exported
        self._active = False
        assert isinstance(context, context_.Context) or context is None
        self._context = context
        self._grammar = None

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._name)

    #-----------------------------------------------------------------------
    # Protected attribute access.

    name = property(lambda self: self._name,
        doc="Read-only access to a rule's name.")

    element = property(lambda self: self._element,
        doc="Read-only access to a rule's root element.")

    exported = property(lambda self: self._exported,
        doc="Read-only access to the exported attribute.")

    imported = property(lambda self: self._imported,
        doc="Read-only access to the imported attribute.")

    def _get_grammar(self):
        return self._grammar
    def _set_grammar(self, grammar):
        if self._grammar is None:
            self._grammar = grammar
        elif grammar != self._grammar:
            raise TypeError("The grammar object a Dragonfly rule"
                " cannot be changed after it has been set (%s != %s)."
                % (grammar, self._grammar))
    grammar = property(_get_grammar, _set_grammar,
        doc="Set-once access to a rule's grammar object.")

    #-----------------------------------------------------------------------
    # Internal methods for controlling a rules active state.

    def process_begin(self, executable, title, handle):
        assert self._grammar
        if self._context:
            if self._context.matches(executable, title, handle):
                self.activate()
                self._process_begin()
            else:
                self.deactivate()
        else:
            self.activate()
            self._process_begin()

    def activate(self):
        if not self._grammar:
            raise TypeError("A Dragonfly rule cannot be activated"
                            " before it is bound to a grammar.")
        if not self._active:
            self._grammar.activate_rule(self)
            self._active = True

    def deactivate(self):
        if not self._grammar:
            raise TypeError("A Dragonfly rule cannot be deactivated"
                            " before it is bound to a grammar.")
        if self._active:
            self._grammar.deactivate_rule(self)
            self._active = False

    active = property(lambda self: self._active,
        doc="Read-only access to a rule's active state.")

    exported = property(lambda self: self._exported,
        doc="Read-only access to a rule's exported state.")

    #-----------------------------------------------------------------------
    # Compilation related methods.

    def gstring(self):
        s = "<" + self.name + ">"
        if self.imported: return s + " imported;"
        if self.exported: s += " exported"
        s += " = " + self.element.gstring() + ";"
        return s

    def dependencies(self):
        return self._element.dependencies()

    #-----------------------------------------------------------------------
    # Methods for decoding and evaluating recognitions.

    def decode(self, state):
        state.decode_attempt(self)

        for result in self._element.decode(state):
            state.decode_success(self)
            yield state
            state.decode_retry(self)

        state.decode_failure(self)
        return

    def value(self, node):
        return node.children[0].value()

    #-----------------------------------------------------------------------
    # Methods for processing before-and-after utterances.

    def _process_begin(self):
        pass

    def process_results(self, data):
        pass

    def process_recognition(self, node):
        pass


class ImportedRule(Rule):

    def __init__(self, name):
        self._name = name
        self._imported = True
        self._exported = False
        self._active = False
        self._grammar = None

    #-----------------------------------------------------------------------
    # Compilation related methods.

    def dependencies(self):
        return ()


#---------------------------------------------------------------------------
# Delayed imports.

import dragonfly.grammar.context as context_
