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

from ..base                import RecObsManagerBase
from ...grammar.grammar    import Grammar
from ...grammar.rule_base  import Rule
from ...grammar.elements   import Impossible


#---------------------------------------------------------------------------

class NatlinkRecObsManager(RecObsManagerBase):

    def __init__(self, engine):
        RecObsManagerBase.__init__(self, engine)
        self._grammar = None

        # Define a flag for limiting the number of notify_recognition()
        # calls to one per utterance / mimic call. This is necessary to
        # guarantee that observers are notified *before* rule processing and
        # are still notified about dictation and other grammar recognitions
        # via the special NatlinkRecObsGrammar grammar.
        self._complete_flag = False

    def notify_begin(self):
        super(NatlinkRecObsManager, self).notify_begin()
        self._complete_flag = False

    def notify_recognition(self, words, rule, root, results):
        if self._complete_flag:
            return

        super(NatlinkRecObsManager, self).notify_recognition(words, rule,
                                                             root, results)

    def notify_post_recognition(self, words, rule, root, results):
        if self._complete_flag:
            return

        super(NatlinkRecObsManager, self).notify_post_recognition(
            words, rule, root, results
        )
        self._complete_flag = True

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
    # Callback methods for handling utterances and recognitions.

    def process_begin(self, executable, title, handle):
        self._manager.notify_begin()

    def process_recognition(self, words):
        raise RuntimeError("Recognition observer received an unexpected"
                           " recognition: %s" % (words,))

    def process_recognition_other(self, words, results):
        self._manager.notify_recognition(words, None, None, results)
        self._manager.notify_post_recognition(words, None, None, results)

    def process_recognition_failure(self, results):
        self._manager.notify_failure(results)
