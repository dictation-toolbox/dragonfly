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
    This file implements the compiler class for SAPI 5, used by
    Windows Speech Recognition (WSR).  This is the interface
    built into Windows Vista.
"""


#---------------------------------------------------------------------------

import sys
from win32com.client import constants

from dragonfly.engines.compiler_base import CompilerBase, CompilerError


#---------------------------------------------------------------------------
# Utility generator function for iterating over COM collections.

def collection_iter(collection):
    for index in xrange(0, collection.Count):
        yield collection.Item(index)

_trace_level=0
def trace_compile(func):
    return func
    def dec(self, element, src_state, dst_state, grammar, grammar_handle):
        global _trace_level
        s = '%s %s: compiling %s' % (grammar.name, '==='*_trace_level, element)
        l = 140-len(s)
        s += ' '*l + '| %-20s %s -> %s' % (src_state.Rule.Name, src_state and id(src_state), dst_state and id(dst_state))
        grammar._log_load.error(s)
        _trace_level+=1
        func(self, element, src_state, dst_state, grammar, grammar_handle)
        _trace_level-=1
        grammar._log_load.error('%s %s: compiling %s.' % (grammar.name, '...'*_trace_level, element))
    return dec


#---------------------------------------------------------------------------

class Sapi5Compiler(CompilerBase):

    #-----------------------------------------------------------------------
    # Methods for compiling grammars.

    def compile_grammar(self, grammar, context):
        self._log.debug("%s: Compiling grammar %s." % (self, grammar.name))
        grammar_handle = context.CreateGrammar()

        for rule in grammar.rules:
            self._compile_rule(rule, grammar, grammar_handle)
        grammar_handle.Rules.Commit()

        return grammar_handle

    def _compile_rule(self, rule, grammar, grammar_handle):
        self._log.debug("%s: Compiling rule %s." % (self, rule.name))

        # Determine whether this rule has already been compiled.
        rule_handle = grammar_handle.Rules.FindRule(rule.name)
        if rule_handle:
            self._log.debug("%s: Already compiled rule %s." % (self, rule.name))
            return

        # Generate a new unique rule ID within this grammar.
        if not hasattr(grammar, "_sapi5_next_rule_id"):
            grammar._sapi5_next_rule_id = 1
        rule_id = grammar._sapi5_next_rule_id
        grammar._sapi5_next_rule_id += 1

        # Determine the flags to set when adding this rule.
        flags = 0
        if rule.exported:
            flags |= constants.SRATopLevel

        # Add this rule, and compile its root element.
        rule_handle = grammar_handle.Rules.Add(rule.name, flags, rule_id)
        self._log.debug("%s: Compiling rule %r (id %r)." % (self, rule_handle.Name, rule_handle.Id))
        self.compile_element(rule.element, rule_handle.InitialState, None, grammar, grammar_handle)

        return

        # Below is for debugging purposes only.
        stack = [(collection_iter(rule_handle.InitialState.Transitions), None)]
        while stack:
            self._log.error("%s: Stack len %s." % (self, len(stack)))
            try:
                t = stack[-1][0].next()
            except StopIteration:
                stack.pop()
                continue

            s = t.NextState
            if s:
                stack.append((collection_iter(s.Transitions), t))
            else:
                ts = [j for i,j in stack[1:]] + [t]
                path = [j.Text or j.Rule and ("<%s>" % j.Rule.Name) for j in ts]
                self._log.error("%s: path %r." % (self, path))
            if len(stack) > 100:
                ts = [j for i,j in stack[1:]] + [t]
                path = ["%r[%s]" % (j.Text,j.NextState) or j.Rule and ("<%s>" % j.Rule.Name) for j in ts]
                self._log.error("%s: path %r." % (self, path))
                break


    #-----------------------------------------------------------------------
    # Methods for compiling elements.

    @trace_compile
    def _compile_sequence(self, element, src_state, dst_state, grammar, grammar_handle):
        states = [src_state.Rule.AddState() for i in range(len(element.children)-1)]
        states.insert(0, src_state)
        states.append(dst_state)
        for i, child in enumerate(element.children):
            s1 = states[i]
            s2 = states[i + 1]
            self.compile_element(child, s1, s2, grammar, grammar_handle)

    @trace_compile
    def _compile_alternative(self, element, src_state, dst_state, grammar, grammar_handle):
        for child in element.children:
            self.compile_element(child, src_state, dst_state, grammar, grammar_handle)

    @trace_compile
    def _compile_optional(self, element, src_state, dst_state, grammar, grammar_handle):
        self.compile_element(element.children[0], src_state, dst_state, grammar, grammar_handle)
        src_state.AddWordTransition(dst_state, '')#None)

    @trace_compile
    def _compile_literal(self, element, src_state, dst_state, grammar, grammar_handle):
        src_state.AddWordTransition(dst_state, " ".join(element._words))

    @trace_compile
    def _compile_rule_ref(self, element, src_state, dst_state, grammar, grammar_handle):
        rule_handle = grammar_handle.Rules.FindRule(element.rule.name)
        if not rule_handle:
            grammar.add_rule(element.rule)
            self._compile_rule(element.rule, grammar, grammar_handle)
            rule_handle = grammar_handle.Rules.FindRule(element.rule.name)
            if not rule_handle:
                raise CompilerError("%s: Failed to create rule dependency: %r."
                                    % (self, element.rule.name))

        src_state.AddRuleTransition(dst_state, rule_handle)

    @trace_compile
    def _compile_list_ref(self, element, src_state, dst_state, grammar, grammar_handle):
        list_rule_name = "__list_%s" % element.list.name
        rule_handle = grammar_handle.Rules.FindRule(list_rule_name)
        if not rule_handle:
            grammar.add_list(element.list)
            flags = constants.SRADynamic
            rule_handle = grammar_handle.Rules.Add(list_rule_name, flags, 0)
        src_state.AddRuleTransition(dst_state, rule_handle)

    @trace_compile
    def _compile_dictation(self, element, src_state, dst_state, grammar, grammar_handle):
        rule_handle = self._get_dictation_rule(grammar, grammar_handle)
        src_state.AddRuleTransition(dst_state, rule_handle)

    def _get_dictation_rule(self, grammar, grammar_handle):
        """
            Retrieve the special dictation rule.

            If it already exists within this grammar, return it.
            If it does not yet exist, create it.
        """
        rule_handle = grammar_handle.Rules.FindRule("dgndictation")
        if rule_handle:
#            self._log.error("%s: dictation rule already present." % self)
            return rule_handle
#        self._log.error("%s: building dictation rule ." % self)

        flags = 0
#        flags = constants.SRADynamic
        rule_handle = grammar_handle.Rules.Add("dgndictation", flags, 0)
#        grammar.add_rule(

        src_state = rule_handle.InitialState
        dst_state = None
        src_state.AddSpecialTransition(dst_state, 2)
        states = [src_state.Rule.AddState() for i in range(16)]
        src_state.AddSpecialTransition(states[0], 2)
        for s in states:
            s.AddSpecialTransition(dst_state, 2)
        for s1, s2 in zip(states[:-1], states[1:]):
            s1.AddSpecialTransition(s2, 2)

        return rule_handle
