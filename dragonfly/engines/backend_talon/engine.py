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
import logging

from ..base        import (EngineBase, EngineError, MimicFailure,
                           GrammarWrapperBase, DictationContainerBase,
                           RecObsManagerBase)
from .compiler     import TalonCompiler
from ...grammar import state as state_
from ...windows import Window


class TalonEngine(EngineBase):
    """ Speech recognition engine back-end for Talon. """

    _name = "talon"
    DictationContainer = DictationContainerBase

    def __init__(self):
        super().__init__()
        self._recognition_observer_manager = RecObsManagerBase(self)
        try:
            from talon.experimental.dragonfly import DragonflyInterface
        except ImportError:
            self._log.error("%s: failed to import talon module." % self)
            raise EngineError("Requested engine 'talon' is not available: "
                              "not running under a supported Talon app.")
        self._interface = DragonflyInterface(self.phrase_begin, self.handle_recognition)

    # -----------------------------------------------------------------------
    # Methods for working with grammars.

    def load_grammar(self, grammar):
        # this duplicate reload strategy makes Talon autoreload work
        wrapper = self._grammar_wrappers.get(grammar.name)
        if wrapper is not None:
            if wrapper.grammar == grammar:
                self._log.warning("Grammar %s loaded multiple times." % grammar)
                return
            else:
                self.unload_grammar(wrapper.grammar)

        wrapper = self._load_grammar(grammar)
        # On the base class this dictionary is id -> wrapper,
        # but we prefer to use names
        self._grammar_wrappers[grammar.name] = wrapper

    def _load_grammar(self, grammar):
        """ Load the given *grammar*. """
        self._log.debug("Engine %s: loading grammar %s."
                        % (self, grammar.name))

        c = TalonCompiler()
        rule_dict, exports, rule_refs, list_refs = c.compile_grammar(grammar)
        self._interface.load_grammar(grammar.name, rule_dict, exports, rule_refs, list_refs)
        self._interface.register_cleanup(disable_eval='grammar.unload()',
                                         enable_eval='grammar.load()',
                                         grammar=grammar)

        wrapper = GrammarWrapper(grammar, self, self._recognition_observer_manager)
        return wrapper

    def unload_grammar(self, grammar):
        # this wrapper check makes Talon autoreload work
        wrapper = self._grammar_wrappers.get(grammar.name)
        if wrapper is not None and wrapper.grammar != grammar:
            return
        else:
            wrapper = self._grammar_wrappers.pop(grammar.name)

        if not wrapper:
            raise EngineError("Grammar %s cannot be unloaded because"
                              " it was not loaded." % grammar)
        self._unload_grammar(grammar, wrapper)

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
        self._interface.update_list(grammar.name, lst.name, lst.get_list_items())

    #-----------------------------------------------------------------------
    # Recognition handling

    def phrase_begin(self):
        # Called on phrase begin while engine is paused
        self._recognition_observer_manager.notify_begin()
        fg_window = Window.get_foreground()

        for wrapper in self._iter_all_grammar_wrappers_dynamically():
            wrapper.grammar.process_begin(
                fg_window.executable,
                fg_window.title,
                fg_window.handle
            )

    def handle_recognition(self, grammar_name, words_rules):
        if grammar_name not in self._grammar_wrappers:
            raise EngineError("Trying to handle recognition for grammar '%s', but the grammar is not loaded." % grammar_name)
        wrapper = self._grammar_wrappers[grammar_name]
        wrapper.process_words(words_rules)

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

    def _has_quoted_words_support(self):
        return False

class GrammarWrapper(GrammarWrapperBase):

    _log = logging.getLogger("engine")

    def process_begin(self, executable, title, handle):
        self.grammar.process_begin(executable, title, handle)

    def process_words(self, words_rules):
        # words_rules is a sequence of (word, rule_id) 2-tuples.
        # rule_id - 1_000_000 if dictation else 0
        if not (self.grammar.enabled and self.grammar.active_rules):
            return

        self._log.debug("Grammar %s: received recognition %r."
                        % (self.grammar.name, words_rules))

        results_obj = None
        words = tuple(word for word, _ in words_rules)

        func = getattr(self.grammar, "process_recognition", None)
        if func:
            if not self._process_grammar_callback(func, words=words,
                                                  results=results_obj):
                return

        s = state_.State(words_rules, self.grammar.rule_names, self.engine)
        for r in self.grammar.rules:
            if not (r.active and r.exported):
                continue
            s.initialize_decoding()
            for _ in r.decode(s):
                if s.finished():
                    try:
                        root = s.build_parse_tree()

                        notify_args = (words, r, root, results_obj)
                        self.recobs_manager.notify_recognition(
                            *notify_args
                        )

                        r.process_recognition(root)

                        self.recobs_manager.notify_post_recognition(
                            *notify_args
                        )
                    except Exception as e:
                        self._log.exception("Failed to process rule "
                                            "'%s': %s" % (r.name, e))
                    return True

        self._log.debug("Grammar %s: failed to decode recognition %r."
                        % (self.grammar.name, words))
        return False
