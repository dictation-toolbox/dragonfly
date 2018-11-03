#
# This file is part of Dragonfly.
# (c) Copyright 2018 by Dane Finlay
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

from six import string_types

from .dictation import TextDictationContainer
from .recobs import TextRecobsManager
from ..base import EngineBase, EngineError, MimicFailure


class TextInputEngine(EngineBase):
    """Text-input Engine class. """

    _name = "text"
    DictationContainer = TextDictationContainer

    # -----------------------------------------------------------------------

    def __init__(self):
        EngineBase.__init__(self)
        self._language = "en"
        self._recognition_observer_manager = TextRecobsManager(self)

    def connect(self):
        pass

    def disconnect(self):
        pass

    # -----------------------------------------------------------------------
    # Methods for working with grammars.

    def _build_grammar_wrapper(self, grammar):
        return GrammarWrapper(grammar, self)

    def _load_grammar(self, grammar):
        """ Load the given *grammar* and return a wrapper. """
        self._log.debug("Engine %s: loading grammar %s."
                        % (self, grammar.name))

        grammar.engine = self
        # Dependency checking.
        memo = []
        for r in grammar.rules:
            for d in r.dependencies(memo):
                grammar.add_dependency(d)

        return self._build_grammar_wrapper(grammar)

    def _unload_grammar(self, grammar, wrapper):
        # No engine-specific unloading required.
        pass

    def activate_grammar(self, grammar):
        # No engine-specific grammar activation required.
        pass

    def deactivate_grammar(self, grammar):
        # No engine-specific grammar deactivation required.
        pass

    def activate_rule(self, rule, grammar):
        # No engine-specific rule activation required.
        pass

    def deactivate_rule(self, rule, grammar):
        # No engine-specific rule deactivation required.
        pass

    def update_list(self, lst, grammar):
        # No engine-specific list update is required.
        pass

    def set_exclusiveness(self, grammar, exclusive):
        pass

    # -----------------------------------------------------------------------
    # Miscellaneous methods.

    def mimic(self, words):
        # TODO Implement mimic with fake speech start and hypothesis methods
        pass

    def speak(self, text):
        raise NotImplementedError("text-to-speech is not implemented for "
                                  "this engine")

    @property
    def language(self):
        """
        Current user language of the SR engine.

        :rtype: str
        """
        return self._get_language()

    def _get_language(self):
        return self._language

    @language.setter
    def language(self, value):
        if not isinstance(value, string_types):
            raise TypeError("expected string, not %s" % value)

        self._language = value


class GrammarWrapper(object):
    def __init__(self, grammar, engine):
        self.grammar = grammar
        self.engine = engine
