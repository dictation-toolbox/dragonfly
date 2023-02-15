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


#---------------------------------------------------------------------------

class GrammarWrapperBase(object):

    _log = logging.getLogger("engine")

    # Change to True for back-ends which have trouble differentiating
    #  command and dictation words.
    _dictated_word_guesses_enabled = False

    def __init__(self, grammar, engine):
        self.grammar = grammar
        self.engine = engine

    @property
    def grammar_is_active(self):
        return self.grammar.enabled and any(self.grammar.active_rules)

    def begin_callback(self, executable, title, handle):
        self.grammar.process_begin(executable, title, handle)

    def process_results(self, words, rule_names, results, dispatch_other,
                        *args):
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

        # Attempt to decode and process this grammar's rules.
        state = state_.State(words_rules, rule_names, self.engine)
        success = self._process_grammar_rules(state, words, results,
                                              dispatch_other, *args)

        # If unsuccessful and dictated word guesses are enabled, try again
        #  with that decoding option.
        if not success and self._dictated_word_guesses_enabled:
            state.dictated_word_guesses = True
            success = self._process_grammar_rules(state, words, results,
                                                  dispatch_other, *args)

        return success

    def _process_grammar_rules(self, state, words, results, dispatch_other,
                               *args):
        # Iterate through this grammar's rules, attempting to decode each.
        # If successful, call that rule's method for processing the
        # recognition and return.
        for rule in self.grammar.rules:
            if not (rule.active and rule.exported): continue
            state.initialize_decoding()
            for _ in rule.decode(state):
                if state.finished():
                    self._process_final_rule(state, words, results,
                                             dispatch_other, rule, *args)
                    return True
        return False

    def _process_final_rule(self, state, words, results, dispatch_other,
                            rule, *args):
        # Dispatch results to other grammars, if appropriate.
        if dispatch_other:
            self.engine.dispatch_recognition_other(self.grammar, words,
                                                   results)

        # Call the grammar's general process_recognition method, if it is
        #  present.  Stop if it returns False.
        stop = self.recognition_process_callback(words, results) is False
        if stop: return

        # Process the recognition.
        try:
            root = state.build_parse_tree()
            rule.process_recognition(root)
        except Exception as e:
            self._log.exception("Failed to process rule %r: %s",
                                rule.name, e)

    def recognition_other_callback(self, words, results):
        func = getattr(self.grammar, "process_recognition_other", None)
        if not func: return False
        self._process_grammar_callback(func, words=words, results=results)
        return True

    def recognition_failure_callback(self, results):
        func = getattr(self.grammar, "process_recognition_failure", None)
        if not func: return False
        self._process_grammar_callback(func, results=results)
        return True

    def recognition_process_callback(self, words, results):
        # Call the `process_recognition' callback, if one has been defined.
        # Return True if grammar rule processing should go ahead.
        func = getattr(self.grammar, "process_recognition", None)
        if func:
            result = self._process_grammar_callback(func, words=words,
                                                    results=results)
            return bool(result)
        return None

    def _process_grammar_callback(self, func, **kwargs):
        # Only send keyword arguments that the given function accepts.
        assert callable(func)
        argspec = getargspec(func)
        arg_names, kwargs_names = argspec[0], argspec[2]
        if not kwargs_names:
            kwargs = { k: v for (k, v) in kwargs.items() if k in arg_names }
        try:
            return func(**kwargs)
        except Exception as e:
            self._log.exception("Grammar callback failed with error: %s", e)
