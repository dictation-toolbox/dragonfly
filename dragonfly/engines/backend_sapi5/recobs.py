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
Recognition observer class for the SAPI 5 engine
============================================================================

"""

from ..base                import RecObsManagerBase
from ...grammar.grammar    import Grammar
from ...grammar.rule_base  import Rule
from ...grammar.elements   import Impossible


#---------------------------------------------------------------------------

class Sapi5RecObsManager(RecObsManagerBase):

    def __init__(self, engine):
        RecObsManagerBase.__init__(self, engine)
        self._grammar = Sapi5RecObsGrammar(self)

    def _activate(self):
        self._grammar.load()

    def _deactivate(self):
        self._grammar.unload()


#---------------------------------------------------------------------------

class Sapi5RecObsGrammar(Grammar):

    def __init__(self, manager):
        self._manager = manager
        name = "_recobs_grammar"
        Grammar.__init__(self, name, description=None, context=None)

        rule = Rule(element=Impossible(), exported=True)
        self.add_rule(rule)

    #-----------------------------------------------------------------------
    # Callback methods for handling utterances and recognitions.
    # This grammar does not receive recognized words due to a limitation
    # with WSR. The engine instead notifies observers by using the grammar
    # that successfully recognized the words, if any words were recognized.

    def process_begin(self, executable, title, handle):
        self._manager.notify_begin()

    def process_recognition(self, words):
        # Successfully recognising this grammar should be impossible.
        raise RuntimeError("Recognition observer received an unexpected"
                           " recognition: %s" % (words,))

    def process_recognition_failure(self, results):
        self._manager.notify_failure(results)
