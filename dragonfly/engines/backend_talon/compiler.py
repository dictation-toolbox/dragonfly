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
    This file implements the compiler class for Talon.
"""


from ..base import CompilerBase, CompilerError

import dragonfly.grammar.elements as elements_


class TalonCompiler(CompilerBase):
    def __init__(self):
        super().__init__()
        self._rule_stack = []

    def compile_grammar(self, grammar):
        self._log.debug("%s: Compiling grammar %s." % (self, grammar.name))

        rules = {}
        rule_exports = set()
        for rule in grammar.rules:
            name = 'dragonfly::{}::{}'.format(grammar.name, rule.name)
            pieces = []
            self.compile_element(rule.element, pieces)
            rules[name] = ' '.join(pieces)
            if rule.exported:
                rule_exports.add(name)

        return rules, rule_exports

    #-----------------------------------------------------------------------
    # Methods for compiling elements.

    def _compile_sequence(self, element, pieces):
        for child in element.children:
            self.compile_element(child, pieces)
        is_rep = isinstance(element, elements_.Repetition)
        if is_rep:
            pieces.append('+')
        return [' '.join(pieces)]

    def _compile_alternative(self, element, pieces):
        tmp = []
        for child in element.children:
            child_pieces = []
            self.compile_element(child, child_pieces)
            tmp.append(' '.join(child_pieces))
        pieces.append(' | '.join(tmp))

    def _compile_optional(self, element, pieces):
        tmp = []
        self.compile_element(element.children[0], tmp)
        pieces.append('[' + (' '.join(tmp)) + ']')

    def _compile_literal(self, element, pieces):
        words = ' '.join(element.words_ext)
        pieces.append(words)

    def _compile_rule_ref(self, element, pieces):
        # FIXME: dragonfly vs talon rule names?
        # OLD: compiler.add_rule(element.rule.name, imported=element.rule.imported)
        pieces.append('<' + element.rule.name + '>')

    def _compile_list_ref(self, element, pieces):
        # FIXME: dragonfly vs talon list names?
        pieces.append('{' + element.list.name + '}')

    def _compile_dictation(self, element, pieces):
        pieces.append('<phrase>')

    def _compile_impossible(self, element, pieces):
        pieces.append('{::impossible}')

    def _compile_empty(self, element, pieces):
        pass
