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
Recognition observer class for the Natlink engine
============================================================================

"""

from .recobs_base         import RecObsManagerBase
from ..grammar.grammar    import Grammar
from ..grammar.rule_base  import Rule
from ..grammar.elements   import Impossible


#---------------------------------------------------------------------------

class NatlinkRecObsManager(RecObsManagerBase):

    def __init__(self, engine):
        RecObsManagerBase.__init__(self, engine)
        self._grammar = None

    def _activate(self):
        if not self._grammar:
            self._grammar = NatlinkRecObsGrammar(self)
        self._grammar.load()

    def _deactivate(self):
        if self._grammar:
            self._grammar.unload()
        self._grammar = None


#---------------------------------------------------------------------------

class NatlinkRecObsGrammar(Grammar):

    def __init__(self, manager):
        self._manager = manager
        name = "_recobs_grammar"
        Grammar.__init__(self, name, description=None, context=None)

        rule = Rule(element=Impossible(), exported=True)
        self.add_rule(rule)

    #-----------------------------------------------------------------------
    # Methods for registering a grammar object instance in natlink.

    def load(self):
        """ Load this grammar into its SR engine. """

        # Prevent loading the same grammar multiple times.
        if self._loaded: return
        self._log_load.debug("Grammar %s: loading." % self._name)

        self._engine.load_natlink_grammar(self, all_results=True)
        self._loaded = True
        self._in_context = False

        # Update all lists loaded in this grammar.
        for rule in self._rules:
            if rule.active != False:
                rule.activate()
        # Update all lists loaded in this grammar.
        for lst in self._lists:
            lst._update()

    #-----------------------------------------------------------------------
    # Callback methods for handling utterances and recognitions.

    def process_begin(self, executable, title, handle):
        self._manager.notify_begin()

    def process_results(self, words, result):
        if words == "other":
            words = result.getWords(0)
            self._manager.notify_recognition(result, words)
        else:
            self._manager.notify_failure(result)
        return False
