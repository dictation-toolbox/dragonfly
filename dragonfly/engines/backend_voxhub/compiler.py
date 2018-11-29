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
    This file implements the compiler class for Voxhub.
"""


#---------------------------------------------------------------------------

import struct
from six import string_types, text_type, PY2

from ..base import CompilerBase, CompilerError


#===========================================================================

class VoxhubCompiler(CompilerBase):

    #-----------------------------------------------------------------------
    # Methods for compiling grammars.

    def compile_grammar(self, grammar):
        self._log.debug("%s: Compiling grammar %s." % (self, grammar.name))

        compiler = _Compiler()
        for rule in grammar.rules:
            self._compile_rule(rule, compiler)

        #compiled_grammar = compiler.compile()
        #rule_names = compiler.rule_names
#        print compiler.debug_state_string()
        #return (compiled_grammar, rule_names)
        return True

    def _compile_rule(self, rule, compiler):
        self._log.debug("%s: Compiling rule %s." % (self, rule.name))
        if rule.imported:
            return
        compiler.start_rule_definition(rule.name, exported=rule.exported)
        self.compile_element(rule.element, compiler)
        compiler.end_rule_definition()

    #-----------------------------------------------------------------------
    # Methods for compiling elements.

    def _compile_sequence(self, element, compiler):
        children = element.children
        if len(children) > 1:
            compiler.start_sequence()
            for c in children:
                self.compile_element(c, compiler)
            compiler.end_sequence()
        elif len(children) == 1:
            self.compile_element(children[0], compiler)

    def _compile_alternative(self, element, compiler):
        children = element.children
        if len(children) > 1:
            compiler.start_alternative()
            for c in children:
                self.compile_element(c, compiler)
            compiler.end_alternative()
        elif len(children) == 1:
            self.compile_element(children[0], compiler)

    def _compile_optional(self, element, compiler):
        compiler.start_optional()
        self.compile_element(element.children[0], compiler)
        compiler.end_optional()

    def _compile_literal(self, element, compiler):
        words = element.words
        if len(words) == 1:
            compiler.add_word(words[0])
        elif len(words) > 1:
            compiler.start_sequence()
            for w in words:
                compiler.add_word(w)
            compiler.end_sequence()

    def _compile_rule_ref(self, element, compiler):
        compiler.add_rule(element.rule.name, imported=element.rule.imported)

    def _compile_list_ref(self, element, compiler):
        compiler.add_list(element.list.name)

    def _compile_dictation(self, element, compiler):
        compiler.add_rule("dgndictation", imported=True)

    def _compile_impossible(self, element, compiler):
        compiler.add_list("_empty_list")

    def _compile_empty(self, element, compiler):
        pass


#===========================================================================
# Internal compiler class which takes care of the binary format
#  used to specify grammars with Dragon NaturallySpeaking.

class _Compiler(object):
    def __init__(self):
        self.indent = 0

    def log(self, message):
        print '    '*self.indent + message

    #-----------------------------------------------------------------------

    def start_rule_definition(self, name, exported=False):
        self.log("rule " + name + " {")
        self.indent += 1

    def end_rule_definition(self):
        self.indent -= 1
        self.log("}  // end rule")

    #-----------------------------------------------------------------------
    # Compound structures in a rule definition.

    def start_sequence(self):
        self.log("(")
        self.indent += 1

    def end_sequence(self):
        self.indent -= 1
        self.log(")")

    def start_alternative(self):
        self.log("[|")
        self.indent += 1

    def end_alternative(self):
        self.indent -= 1
        self.log("|]")

    def start_repetition(self):
        self.log("(*")
        self.indent += 1

    def end_repetition(self):
        self.indent -= 1
        self.log("*)")

    def start_optional(self):
        self.log("[")
        self.indent += 1

    def end_optional(self):
        self.indent -= 1
        self.log("]")

    #-----------------------------------------------------------------------
    # Terminal elements in a rule definition.

    def add_word(self, word):
        self.log('"' + word + '"')

    def add_list(self, list):
        self.log(str(list))

    def add_rule(self, rule, imported = False):
        self.log("*ref " + rule)
