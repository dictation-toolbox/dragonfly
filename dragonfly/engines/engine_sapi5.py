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
    This file implements the SAPI 5 engine class.
"""


#---------------------------------------------------------------------------

import win32com.client

from dragonfly.engines.engine_base     import EngineBase
from dragonfly.engines.compiler_sapi5  import Sapi5Compiler


#---------------------------------------------------------------------------

class Sapi5Engine(EngineBase):

    def __init__(self):
        self._recognizer = win32com.client.Dispatch("SAPI.SpSharedRecognizer")
        self._compiler = Sapi5Compiler()


    #-----------------------------------------------------------------------
    # Methods for working with grammars.

    def load_grammar(self, grammar):
        self._log.error("Loading grammar %s." % grammar.name)
        grammar.engine = self
        (context, grammar_handle) = self._compiler.compile_grammar(grammar, self._recognizer)
        self._set_grammar_handle(grammar, grammar_handle)

        self.context = context

    def activate_grammar(self, grammar):
        self._log.error("Activating grammar %s." % grammar.name)
        grammar_handle = self._get_grammar_handle(grammar)
        grammar_handle.DictationSetState(0)

    def activate_rule(self, rule, grammar):
        self._log.error("Activating rule %s in grammar %s." % (rule.name, grammar.name))
        grammar_handle = self._get_grammar_handle(grammar)
        grammar_handle.Rules.Commit()
        grammar_handle.CmdSetRuleState(rule.name, 1)
        grammar_handle.Rules.CommitAndSave()

    def _set_grammar_handle(self, grammar, grammar_handle):
        grammar._grammar_handle = grammar_handle

    def _get_grammar_handle(self, grammar):
        return grammar._grammar_handle
