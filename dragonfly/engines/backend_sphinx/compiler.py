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
This file implements the compiler for CMU Pocket Sphinx speech recognition
engine.
"""
from .dragonfly2jsgf import Translator, TranslationState
from ..base import CompilerBase

# noinspection PyUnusedLocal


class SphinxJSGFCompiler(CompilerBase):
    translator = Translator()

    # -----------------------------------------------------------------------
    # Methods for compiling grammars.

    def compile_grammar(self, grammar, *args, **kwargs):
        self._log.debug("%s: Compiling grammar %s." % (self, grammar.name))

        jsgf_grammar = self.translator.translate_grammar(grammar)
        return jsgf_grammar

    def _compile_any_element(self, element, *args, **kwargs):
        state = TranslationState(element)
        expansion = self.translator.get_jsgf_equiv(state).expansion
        return expansion.compile()

    _compile_sequence     = _compile_any_element
    _compile_alternative  = _compile_any_element
    _compile_optional     = _compile_any_element
    _compile_literal      = _compile_any_element
    _compile_rule_ref     = _compile_any_element
    _compile_list_ref     = _compile_any_element
    _compile_dictation    = _compile_any_element
    _compile_impossible   = _compile_any_element
    _compile_empty        = _compile_any_element

    def _compile_unknown_element(self, element, *args, **kwargs):
        raise NotImplementedError("Compiler %s not implemented for element "
                                  "type %s." % (self, element))
