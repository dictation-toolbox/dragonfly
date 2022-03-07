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
GrammarWrapperBase class
============================================================================

"""

import logging

try:
    from inspect import getfullargspec as getargspec
except ImportError:
    # Fallback on the deprecated function.
    from inspect import getargspec

from dragonfly.grammar import state as state_


class GrammarWrapperBase(object):

    _log = logging.getLogger("engine")

    # Change to True for SR back-ends which have trouble differentiating
    # command and dictation words.
    _dictated_word_guesses_enabled = False

    def __init__(self, grammar, engine, recobs_manager):
        self.grammar = grammar
        self.engine = engine
        self.recobs_manager = recobs_manager

    @property
    def grammar_is_active(self):
        return self.grammar.enabled and any(self.grammar.active_rules)

    def _process_grammar_callback(self, func, **kwargs):
        if not func: return

        # Only send keyword arguments that the given function accepts.
        argspec = getargspec(func)
        arg_names, kwargs_names = argspec[0], argspec[2]
        if not kwargs_names:
            kwargs = { k: v for (k, v) in kwargs.items() if k in arg_names }

        return func(**kwargs)

    def process_begin(self, executable, title, handle):
        self.grammar.process_begin(executable, title, handle)

    def process_special_results(self, type_, words, results):
        # FIXME These special methods are not usually called.
        # These should be used by all engine back-ends for recobs events, as
        # was done originally.  It would be cleaner.
        if type_ == "other":
            func = getattr(self.grammar, "process_recognition_other", None)
            self._process_grammar_callback(func, words=words,
                                           results=results)
            return True
        elif type_ == "reject":
            func = getattr(self.grammar, "process_recognition_failure",
                           None)
            self._process_grammar_callback(func, results=results)
            return True
        return False

    def _decode_grammar_rules(self, state, words, results, *args):
        # Iterate through this grammar's rules, attempting to decode each.
        # If successful, call that rule's method for processing the
        # recognition and return.
        for rule in self.grammar.rules:
            if not (rule.active and rule.exported): continue
            state.initialize_decoding()
            for _ in rule.decode(state):
                if state.finished():
                    # TODO Use words="other" instead, with a special
                    # recobs grammar wrapper at index 0.
                    # Notify observers using the manager *before*
                    # processing.
                    root = state.build_parse_tree()
                    notify_args = (words, rule, root, results)
                    self.recobs_manager.notify_recognition(
                        *notify_args
                    )
                    try:
                        rule.process_recognition(root)
                    except Exception as e:
                        self._log.exception("Failed to process rule "
                                            "'%s': %s" % (rule.name, e))
                    self.recobs_manager.notify_post_recognition(
                        *notify_args
                    )
                    return True
        return False

    def process_results(self, words, rule_names, results, *args):
        # Disabled grammars cannot process recognitions.
        if not self.grammar.enabled:
            return False

        # Special result words *must* be handled separately by each
        #  back-end.
        assert words != "other" and words != "reject"

        # If the words argument was not "other" or "reject", then it is a
        #  sequence of (word, rule_id) 2-tuples.
        words_rules = tuple(words)
        words = tuple(r[0] for r in words)

        # Call the grammar's general process_recognition method, if present.
        func = getattr(self.grammar, "process_recognition", None)
        if func:
            if not self._process_grammar_callback(func, words=words,
                                                  results=results):
                return True

        # Attempt to decode this grammar's rules.
        state = state_.State(words_rules, rule_names, self.engine)
        success = self._decode_grammar_rules(state, words, results, *args)

        # If unsuccessful and dictated word guesses are enabled, try again
        #  with that decoding option.
        if not success and self._dictated_word_guesses_enabled:
            state.dictated_word_guesses = True
            success = self._decode_grammar_rules(state, words, results,
                                                 *args)

        return success
