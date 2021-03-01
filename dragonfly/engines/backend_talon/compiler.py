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

from talon.experimental.dragonfly import DragonflyInterface


class TalonCompilerState:
    def __init__(self, grammar):
        self.grammar = grammar
        self.path = DragonflyInterface.get_path(grammar.name)
        self.rule_refs = set()
        self.list_refs = set()

class TalonCompiler(CompilerBase):
    def __init__(self):
        super().__init__()
        self._rule_stack = []

    def compile_grammar(self, grammar):
        self._log.debug("%s: Compiling grammar %s." % (self, grammar.name))

        state = TalonCompilerState(grammar)
        rules = {}
        rule_exports = set()
        for rule in grammar.rules:
            rule_name = DragonflyInterface.sanitize_name(rule.name)
            pieces = []
            self.compile_element(rule.element, state, pieces)
            rules[rule_name] = ' '.join(pieces)
            if rule.exported:
                rule_exports.add(rule_name)

        return rules, rule_exports, state.rule_refs, state.list_refs

    #-----------------------------------------------------------------------
    # Methods for compiling elements.

    def _compile_sequence(self, element, state, pieces):
        for child in element.children:
            self.compile_element(child, state, pieces)
        is_rep = isinstance(element, elements_.Repetition)
        if is_rep:
            pieces.append('+')
        return [' '.join(pieces)]

    def _compile_alternative(self, element, state, pieces):
        tmp = []
        for child in element.children:
            child_pieces = []
            self.compile_element(child, state, child_pieces)
            tmp.append(' '.join(child_pieces))
        pieces.append('(' + ' | '.join(tmp) + ')')

    def _compile_optional(self, element, state, pieces):
        tmp = []
        self.compile_element(element.children[0], state, tmp)
        pieces.append('[' + ' '.join(tmp) + ']')

    def _compile_literal(self, element, state, pieces):
        words = ' '.join(element.words_ext)
        pieces.append(words)

    def _compile_rule_ref(self, element, state, pieces):
        name = DragonflyInterface.sanitize_name(element.rule.name)
        rule_path = '{}_{}'.format(state.path, name)
        pieces.append('<' + rule_path + '>')
        state.rule_refs.add(name)

    def _compile_list_ref(self, element, state, pieces):
        name = DragonflyInterface.sanitize_name(element.list.name)
        list_path = '{}_{}'.format(state.path, name)
        pieces.append('{' + list_path + '}')
        state.list_refs.add(name)

    def _compile_dictation(self, element, state, pieces):
        pieces.append('<phrase>')

    def _compile_impossible(self, element, state, pieces):
        pieces.append('{::impossible}')

    def _compile_empty(self, element, state, pieces):
        pass
