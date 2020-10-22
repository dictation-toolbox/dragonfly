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
"""

import unittest
from .rule_test_grammar     import RuleTestGrammar
from ..engines              import get_engine


#===========================================================================

class RuleTestCase(unittest.TestCase):
    """
    """

    def run(self, result=None):
        self.engine = get_engine()
        self.grammar = RuleTestGrammar()
        return unittest.TestCase.run(self, result)

    def tearDown(self):
        self.grammar.unload()
        for rule in self.grammar.rules:
            self.grammar.remove_rule(rule)
        for lst in self.grammar.lists:
            self.grammar.remove_list(lst)

    def add_rule(self, rule):
        self.grammar.add_rule(rule)

    def recognize(self, words):
        return self.grammar.recognize(words)

    def recognize_node(self, words):
        return self.grammar.recognize_node(words)

    def recognize_extras(self, words):
        return self.grammar.recognize_extras(words)
