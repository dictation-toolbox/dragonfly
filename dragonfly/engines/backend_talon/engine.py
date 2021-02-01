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
SR back-end for Talon
"""
from ..base        import (EngineBase, EngineError, MimicFailure,
                           GrammarWrapperBase)
from .compiler     import TalonCompiler


class TalonEngine(EngineBase):
    """ Speech recognition engine back-end for Talon. """

    _name = "talon"
    # DictationContainer = TalonDictationContainer

    def __init__(self):
        super().__init__()
        try:
            from talon.lib.dragonfly import DragonflyInterface
        except ImportError:
            self._log.error("%s: failed to import talon module." % self)
            raise EngineError("Requested engine 'talon' is not available: "
                              "not running under a supported Talon app.")
        self._interface = DragonflyInterface(self)

    # -----------------------------------------------------------------------
    # Methods for working with grammars.

    def _load_grammar(self, grammar):
        """ Load the given *grammar*. """
        self._log.debug("Engine %s: loading grammar %s."
                        % (self, grammar.name))

        c = TalonCompiler()
        grammar_dict = c.compile_grammar(grammar)
        self._interface.load_grammar(grammar.name, grammar_dict)

    def _unload_grammar(self, grammar, wrapper):
        """ Unload the given *grammar*. """
        self._interface.unload_grammar(grammar.name)

    def set_exclusiveness(self, grammar, exclusive):
        pass # FIXME?

    def activate_grammar(self, grammar):
        pass

    def deactivate_grammar(self, grammar):
        pass

    def activate_rule(self, rule, grammar):
        self._log.debug("Activating rule %s in grammar %s." % (rule.name, grammar.name))
        self._interface.activate_rule(grammar.name, rule.name)

    def deactivate_rule(self, rule, grammar):
        self._log.debug("Deactivating rule %s in grammar %s." % (rule.name, grammar.name))
        self._interface.deactivate_rule(grammar.name, rule.name)

    def update_list(self, lst, grammar):
        self._interface.set_list(grammar.name, lst.name, lst.get_list_items())

    #-----------------------------------------------------------------------
    # Miscellaneous methods.

    def mimic(self, words):
        """
        Mimic a recognition of the given *words*.
        """
        self._interface.mimic(words)

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        self._interface.speak(text)

    def _get_language(self):
        return self._interface.get_language()
