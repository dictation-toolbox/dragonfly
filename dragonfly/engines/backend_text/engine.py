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

from six import string_types, text_type

import dragonfly.grammar.state as state_
from dragonfly import Window

from .dictation import TextDictationContainer
from .recobs import TextRecobsManager
from ..base import EngineBase, EngineError, MimicFailure


def _map_word(word):
    word = text_type(word)
    if word.isupper():
        # Convert dictation words to lowercase for consistent output.
        return word.lower(), 1000000
    else:
        return word, 0


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
        # Clear grammar wrappers on disconnect()
        self._grammar_wrappers.clear()

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
        # Disable/enable each grammar.
        for g in self.grammars:
            if exclusive:
                g.disable()
            else:
                g.enable()

        # Enable the specified grammar if it was supposed to be exclusive.
        if exclusive:
            grammar.enable()

    # -----------------------------------------------------------------------
    # Miscellaneous methods.

    @classmethod
    def generate_words_rules(cls, words):
        # Convert words to Unicode, treat all uppercase words as dictation
        # words and other words as grammar words.
        # Minor note: this won't work for languages without capitalisation.
        return tuple(map(_map_word, words))

    def mimic(self, words):
        """ Mimic a recognition of the given *words*. """
        # Handle string input.
        if isinstance(words, string_types):
            words = words.split()

        # Don't allow non-iterable objects.
        if not iter(words):
            raise TypeError("%r is not a string or other iterable object"
                            % words)

        # Notify observers that a recognition has begun.
        self._recognition_observer_manager.notify_begin()

        # Generate the input for process_words.
        words_rules = self.generate_words_rules(words)

        # Call process_begin and process_words for all grammar wrappers,
        # stopping early if processing occurred.
        fg_window = Window.get_foreground()
        processing_occurred = False
        for wrapper in self._grammar_wrappers.values():
            wrapper.process_begin(fg_window)
            processing_occurred = wrapper.process_words(words_rules)
            if processing_occurred:
                # Notify observers of the recognition.
                self._recognition_observer_manager.notify_recognition(
                    [word for word, _ in words_rules]
                )
                break

        # If no processing occurred, then the mimic failed.
        if not processing_occurred:
            self._recognition_observer_manager.notify_failure()
            raise MimicFailure("No matching rule found for words %r."
                               % (words,))

    def speak(self, text):
        self._log.warning("text-to-speech is not implemented for this "
                          "engine.")
        self._log.warning("Printing text instead.")
        print(text)

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

    def process_begin(self, fg_window):
        self.grammar.process_begin(fg_window.executable, fg_window.title,
                                   fg_window.handle)

    def process_words(self, words):
        # Return early if the grammar is disabled or if there are no active
        # rules.
        if not (self.grammar.enabled and self.grammar.active_rules):
            return

        TextInputEngine._log.debug("Grammar %s: received recognition %r."
                                   % (self.grammar.name, words))
        if words == "other":
            func = getattr(self.grammar, "process_recognition_other", None)
            if func:
                func(words)
            return
        elif words == "reject":
            func = getattr(self.grammar, "process_recognition_failure", None)
            if func:
                func()
            return

        # If the words argument was not "other" or "reject", then it is a
        # sequence of (word, rule_id) 2-tuples.
        # Call the grammar's general process_recognition method, if present.
        func = getattr(self.grammar, "process_recognition", None)
        if func:
            if not func(words):
                return

        # Iterate through this grammar's rules, attempting to decode each.
        # If successful, call that rule's method for processing the
        # recognition and return.
        s = state_.State(words, self.grammar.rule_names, self.engine)
        for r in self.grammar.rules:
            if not r.active:
                continue
            s.initialize_decoding()
            for _ in r.decode(s):
                if s.finished():
                    root = s.build_parse_tree()
                    r.process_recognition(root)
                    return True

        TextInputEngine._log.debug("Grammar %s: failed to decode "
                                   "recognition %r."
                                   % (self.grammar.name, words))
        return False
