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

from dragonfly.engines.compiler_base import CompilerBase


#---------------------------------------------------------------------------

class Sapi5Compiler(CompilerBase):

    #-----------------------------------------------------------------------
    # Methods for compiling grammars.

    def compile_grammar(self, grammar, recognizer):
        self._log.error("%s: Compiling grammar %s." % (self, grammar.name))
        context = recognizer.CreateRecoContext()
        grammar_handle = context.CreateGrammar()

        for rule in grammar.rules:
            self._compile_rule(rule, grammar_handle)

        return (context, grammar_handle)

    def _compile_rule(self, rule, grammar_handle):
        self._log.error("%s: Compiling rule %s." % (self, rule.name))

        flags = constants.SRATopLevel + constants.SRADynamic
        rule_handle = grammar_handle.Rules.Add(rule.name, flags, 0)
        self.compile_element(rule.element, rule_handle.InitialState, None)

    #-----------------------------------------------------------------------
    # Methods for compiling elements.

    def _compile_sequence(self, element, src_state, dst_state):
        self._log.error("%s: Compiling element %s." % (self, element))

        states = [src_state.Rule.AddState() for i in range(len(element.children)-1)]
        states.insert(0, src_state)
        states.append(dst_state)
        for i, child in enumerate(element.children):
            s1 = states[i]
            s2 = states[i + 1]
            self.compile_element(child, s1, s2)

    def _compile_alternative(self, element, src_state, dst_state):
        self._log.error("%s: Compiling element %s." % (self, element))

        for child in element.children:
            self.compile_element(child, src_state, dst_state)

    def _compile_optional(self, element, src_state, dst_state):
        self._log.error("%s: Compiling element %s." % (self, element))

        self.compile_element(element, src_state, dst_state)
        src_state.AddWordTransition(dst_state, None)

    def _compile_literal(self, element, src_state, dst_state):
        self._log.error("%s: Compiling element %s." % (self, element))

        src_state.AddWordTransition(dst_state, " ".join(element._words))
