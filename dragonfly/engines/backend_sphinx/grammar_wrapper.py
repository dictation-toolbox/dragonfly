#
# This file is part of Dragonfly.
# (c) Copyright 2018-2022 by Dane Finlay
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
GrammarWrapper class for the CMU Pocket Sphinx engine
============================================================================

"""

import logging

from dragonfly.engines.base import GrammarWrapperBase


#---------------------------------------------------------------------------

class GrammarWrapper(GrammarWrapperBase):

    # Enable guessing at the type of a given result word.
    _dictated_word_guesses_enabled = False

    def __init__(self, grammar, engine, search_name):
        """
        :type grammar: Grammar
        :type engine: SphinxEngine
        """
        GrammarWrapperBase.__init__(self, grammar, engine)
        self.set_search = True
        self._search_name = search_name
        self.exclusive = False

        # Compile the grammar into a JSGF grammar and set the language.
        self._jsgf_grammar = engine.compiler.compile_grammar(grammar)
        self._jsgf_grammar.language_name = engine.language

    def _get_reference_name(self, name):
        return self.engine.compiler.get_reference_name(name)

    def enable_rule(self, name):
        ref_name = self._get_reference_name(name)
        jsgf_rule = self._jsgf_grammar.get_rule_from_name(ref_name)

        # Only enable the rule and set the flag if the rule is disabled.
        if not jsgf_rule.active:
            jsgf_rule.enable()
            self.set_search = True

    def disable_rule(self, name):
        ref_name = self._get_reference_name(name)
        jsgf_rule = self._jsgf_grammar.get_rule_from_name(ref_name)

        # Only disable the rule and set the flag if the rule is enabled.
        if jsgf_rule.active:
            jsgf_rule.disable()
            self.set_search = True

    def update_list(self, lst):
        # Recompile the list again.
        grammar = self._jsgf_grammar
        name = self._get_reference_name(lst.name)
        old_rule = grammar.get_rule_from_name(name)
        new_rule, unknown_words = self.engine.compiler.recompile_list(
            lst, grammar
        )

        # Only replace the old rule if the list has changed.
        if old_rule != new_rule:
            grammar.remove_rule(old_rule, ignore_dependent=True)
            grammar.add_rule(new_rule)
            self.set_search = True

            # Log a warning about unknown words if necessary.
            if unknown_words:
                logger = logging.getLogger("engine.compiler")
                logger.warning("List '%s' used words not found in the "
                               "pronunciation dictionary: %s", name,
                               ", ".join(sorted(unknown_words)))

    def compile_jsgf(self):
        return self._jsgf_grammar.compile_as_root_grammar()

    @property
    def search_name(self):
        """
        The name of the Pocket Sphinx search that the engine should use to
        process speech for the grammar.

        :return: str
        """
        return self._search_name

    def set_dictated_word_guesses(self, value):
        self._dictated_word_guesses_enabled = value

    def _process_final_rule(self, state, words, results, dispatch_other,
                            rule, *args):
        # Recognition successful!  Set the results data.
        results.type = args[0]
        results.rule = rule
        results.grammar = self.grammar

        # Call the base class method.
        GrammarWrapperBase._process_final_rule(self, state, words, results,
                                               dispatch_other, rule, *args)
