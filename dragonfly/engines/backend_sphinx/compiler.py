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
    This file implements the compiler for CMU Sphinx voice recognition engine.
"""

from dragonfly.engines.compiler_natlink import NatlinkCompiler
from dragonfly.engines.compiler_natlink import _Compiler as NatlinkInternalCompiler

# import dragonfly.grammar.elements as elements_
# from ..base import CompilerBase


class SphinxCompiler(NatlinkCompiler):
    def compile_grammar(self, grammar, *args, **kwargs):
        self._log.debug("%s: Compiling grammar %s." % (self, grammar.name))

        compiler = _Compiler()
        for rule in grammar.rules:
            self._compile_rule(rule, compiler)

        compiled_grammar = compiler.compile()
        rule_names = compiler.rule_names
        #        print compiler.debug_state_string()
        return compiled_grammar, rule_names

    def _compile_unknown_element(self, element, *args, **kwargs):
        pass


# Internal compiler class for CMU Sphinx/PocketSphinx
class _Compiler(NatlinkInternalCompiler):
    def __init__(self):
        pass
