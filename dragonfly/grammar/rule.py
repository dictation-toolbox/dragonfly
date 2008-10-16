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
import state as state_
import compiler as compiler_
import context as context_


class Rule(object):

    _log_load = log_.get_log("grammar.load")
    _log_eval = log_.get_log("grammar.eval")
    _log_proc = log_.get_log("grammar.process")

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

    def _get_grammar(self):
        return self._grammar
    def _set_grammar(self, grammar):
        if self._grammar is None:
            self._grammar = grammar
        else:
            raise TypeError("The grammar object a Dragonfly rule"
                " is bound to cannot be changed after it has been set.")
    grammar = property(_get_grammar, _set_grammar,
        doc="Set-once access to a rule's grammar object.")

    #-----------------------------------------------------------------------
    # Internal methods for controlling a rules active state.

    def i_process_begin(self, executable, title, handle):
        assert self._grammar
        if self._context:
            if self._context.matches(executable, title, handle):
                self.activate()
                self.process_begin()
            else:
                self.deactivate()
        else:
            self.activate()
            self.process_begin()

    def activate(self):
        if not self._grammar:
            raise TypeError("A Dragonfly rule cannot be activated"
                            " before it is bound to a grammar.")
        if not self._active:
            self._grammar.i_activate_rule(self)
            self._active = True

    def deactivate(self):
        if not self._grammar:
            raise TypeError("A Dragonfly rule cannot be deactivated"
                            " before it is bound to a grammar.")
        if self._active:
            self._grammar.i_deactivate_rule(self)
            self._active = False

    active = property(lambda self: self._active,
        doc="Read-only access to a rule's active state.")

    exported = property(lambda self: self._exported,
        doc="Read-only access to a rule's exported state.")

    #-----------------------------------------------------------------------
    # Compilation related methods.

    def i_gstring(self):
        s = "<" + self.name + ">"
        if self.imported: return s + " imported;"
        if self.exported: s += " exported"
        s += " = " + self.element.gstring() + ";"
        return s

    def i_dependencies(self):
        return self._element.i_dependencies()

    def i_compile(self, compiler):
        if self._log_load:
            self._log_load.debug("%s: compiling rule:" % self)
            path = [(self._element, 0)]
            self._log_load.debug("%s: %s%s" \
                            % (self, "  " * len(path), path[-1][0]))
            while path:
                e, i = path[-1]
                if len(e.children) > i:
                    path[-1] = (e, i + 1)
                    path.append((e.children[i], 0))
                    self._log_load.debug("%s: %s%s" \
                                % (self, "  " * len(path), path[-1][0]))
                else:
                    path.pop()

        compiler.start_rule_definition(self._name, exported=self._exported)
        self._element.i_compile(compiler)
        compiler.end_rule_definition()

    #-----------------------------------------------------------------------
    # Methods for decoding and evaluating recognitions.

    def i_decode(self, state):
        state.rule_attempt(self)

        for result in self._element.i_decode(state):
            state.rule_success(self)
            yield state
            state.rule_retry(self)

        state.rule_failure(self)
        return

    def i_evaluate(self, node, data):
        if self._log_eval: self._log_eval_debug(node, "evaluating...")
        [c.actor.i_evaluate(c, data) for c in node.children]
        self._evaluate(node, data)

    def _log_eval_debug(self, node, message):
        if self._log_eval:
            self._log_eval.debug("%s%s: %s" \
                                    % ("  "*node.depth, self, message))

    def _evaluate(self, node, data):
        pass

    def value(self, node):
        return node.words()

    #-----------------------------------------------------------------------
    # Methods for processing before-and-after utterances.

    def process_begin(self):
        pass

    def process_results(self, data):
        pass

    def process_recognition(self, node):
        pass
