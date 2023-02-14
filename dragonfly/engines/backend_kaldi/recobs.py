#
# This file is part of Dragonfly.
# (c) Copyright 2018-2023 by Dane Finlay
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
Recognition observer class for the Kaldi engine back-end
============================================================================

"""

from dragonfly.engines.base       import RecObsManagerBase
from dragonfly.grammar.grammar    import Grammar
from dragonfly.grammar.rule_base  import Rule
from dragonfly.grammar.elements   import Impossible


#---------------------------------------------------------------------------

class KaldiRecObsManager(RecObsManagerBase):

    def __init__(self, engine):
        RecObsManagerBase.__init__(self, engine)
        self._grammar = None

    def _activate(self):
        if not self._grammar:
            self._grammar = KaldiRecObsGrammar(self)
        self._grammar.load()

    def _deactivate(self):
        if self._grammar:
            self._grammar.unload()


#---------------------------------------------------------------------------

class KaldiRecObsGrammar(Grammar):

    def __init__(self, manager):
        self._manager = manager
        name = "_recobs_grammar"
        Grammar.__init__(self, name, description=None, context=None)

        rule = Rule(element=Impossible(), exported=True)
        self.add_rule(rule)

    #-----------------------------------------------------------------------
    # Callback methods for handling utterances and recognitions.

    def process_begin(self, executable, title, handle):
        self._manager.notify_begin()

    def process_recognition(self, words):
        raise RuntimeError("Recognition observer received an unexpected"
                           " recognition: %s" % (words,))

    def process_recognition_other(self, words, results):
        self._manager.notify_recognition(words, results)

    def process_recognition_failure(self, results):
        self._manager.notify_failure(results)
