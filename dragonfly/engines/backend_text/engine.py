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

import locale
import logging
import sys
import time

from six import string_types, binary_type

import dragonfly.grammar.state as state_
from dragonfly import Window

from .recobs import TextRecobsManager
from ..base import (EngineBase, MimicFailure, ThreadedTimerManager,
                    DictationContainerBase, GrammarWrapperBase)


def _map_word(word):
    if isinstance(word, binary_type):
        word = word.decode(locale.getpreferredencoding())
    if word.isupper():
        # Convert dictation words to lowercase for consistent output.
        return word.lower(), 1000000
    else:
        return word, 0


class TextInputEngine(EngineBase):
    """Text-input Engine class. """

    _name = "text"
    DictationContainer = DictationContainerBase

    # -----------------------------------------------------------------------

    def __init__(self):
        EngineBase.__init__(self)
        self._language = "en"
        self._connected = False
        self._recognition_observer_manager = TextRecobsManager(self)
        self._timer_manager = ThreadedTimerManager(0.02, self)

    def connect(self):
        self._connected = True

    def disconnect(self):
        # Clear grammar wrappers on disconnect()
        self._grammar_wrappers.clear()
        self._connected = False

    # -----------------------------------------------------------------------
    # Methods for administrating timers.

    def create_timer(self, callback, interval, repeating=True):
        """
        Create and return a timer using the specified callback and repeat
        interval.

        Timers created using this engine will be run in a separate daemon
        thread, meaning that their callbacks will **not** be thread safe.
        :meth:`threading.Timer` may be used instead with no blocking issues.
        """
        return EngineBase.create_timer(self, callback, interval, repeating)

    # -----------------------------------------------------------------------
    # Methods for working with grammars.

    def _build_grammar_wrapper(self, grammar):
        return GrammarWrapper(grammar, self,
                              self._recognition_observer_manager)

    def _load_grammar(self, grammar):
        """ Load the given *grammar* and return a wrapper. """
        self._log.debug("Engine %s: loading grammar %s."
                        % (self, grammar.name))
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
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return

        wrapper.exclusive = exclusive

    # -----------------------------------------------------------------------
    # Miscellaneous methods.

    @classmethod
    def generate_words_rules(cls, words):
        # Convert words to Unicode, treat all uppercase words as dictation
        # words and other words as grammar words.
        # Minor note: this won't work for languages without capitalisation.
        return tuple(map(_map_word, words))

    def _do_recognition(self, delay=0):
        """
        Recognize words from standard input (stdin) in a loop until
        interrupted or :meth:`disconnect` is called.

        :param delay: time in seconds to delay before mimicking each
            command. This is useful for testing contexts.
        """
        self.connect()
        try:
            # Use iter to avoid a bug in Python 2.x:
            # https://bugs.python.org/issue3907
            for line in iter(sys.stdin.readline, ''):
                line = line.strip()
                if not line:  # skip empty lines.
                    continue

                # Delay between mimic() calls if necessary.
                if delay > 0:
                    time.sleep(delay)

                try:
                    self.mimic(line.split())
                except MimicFailure:
                    self._log.error("Mimic failure for words: %s", line)

                # Finish early if disconnect() was called.
                if self._connected is False:
                    break
        except KeyboardInterrupt:
            pass

    def mimic(self, words, **kwargs):
        """
        Mimic a recognition of the given *words*.

        :param words: words to mimic
        :type words: str|iter
        :Keyword Arguments:

           optional *executable*, *title* and/or *handle* keyword arguments
           may be used to simulate a specific foreground window context. The
           current foreground window attributes will be used instead for any
           keyword arguments not present.

        .. note::

           Any dictation words should be all uppercase, e.g. "HELLO WORLD".
           Dictation words not in uppercase will result in the engine
           **not** decoding and recognizing the command!
        """
        # Handle string input.
        if isinstance(words, string_types):
            words = words.split()

        # Don't allow non-iterable objects.
        if not iter(words):
            raise TypeError("%r is not a string or other iterable object"
                            % words)

        # Fail on empty input.
        if not words:
            raise MimicFailure("Invalid mimic input %r" % words)

        # Notify observers that a recognition has begun.
        self._recognition_observer_manager.notify_begin()

        # Generate the input for process_words.
        words_rules = self.generate_words_rules(words)

        w = Window.get_foreground()
        process_args = {
            "executable": w.executable,
            "title": w.title,
            "handle": w.handle,
        }
        # Allows optional passing of window attributes to mimic
        process_args.update(kwargs)

        # Call process_begin() for each grammar wrapper. Use a copy of
        # _grammar_wrappers in case it changes.
        for wrapper in self._grammar_wrappers.copy().values():
            wrapper.process_begin(**process_args)

        # Take another copy of _grammar_wrappers to use for processing.
        grammar_wrappers = self._grammar_wrappers.copy().values()

        # Count exclusive grammars.
        exclusive_count = 0
        for wrapper in grammar_wrappers:
            if wrapper.exclusive:
                exclusive_count += 1

        # Call process_words() for each grammar wrapper, stopping early if
        # processing occurred.
        processing_occurred = False
        for wrapper in grammar_wrappers:
            # Skip non-exclusive grammars if there are one or more exclusive
            # grammars.
            if exclusive_count > 0 and not wrapper.exclusive:
                continue

            # Process the grammar.
            processing_occurred = wrapper.process_words(words_rules)
            if processing_occurred:
                break

        # If no processing occurred, then the mimic failed.
        if not processing_occurred:
            self._recognition_observer_manager.notify_failure(None)
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

    def _has_quoted_words_support(self):
        return False


class GrammarWrapper(GrammarWrapperBase):

    _log = logging.getLogger("engine")

    def __init__(self, grammar, engine, recobs_manager):
        GrammarWrapperBase.__init__(self, grammar, engine, recobs_manager)
        self.exclusive = False

    def process_begin(self, executable, title, handle):
        self.grammar.process_begin(executable, title, handle)

    def process_words(self, words):
        # Return early if the grammar is disabled or if there are no active
        # rules.
        if not (self.grammar.enabled and self.grammar.active_rules):
            return

        self._log.debug("Grammar %s: received recognition %r."
                        % (self.grammar.name, words))

        # TODO Make special grammar callbacks work properly.
        # These special methods are never called for this engine.
        results_obj = None
        if words == "other":
            func = getattr(self.grammar, "process_recognition_other", None)
            self._process_grammar_callback(func, words=words,
                                           results=results_obj)
            return
        elif words == "reject":
            func = getattr(self.grammar, "process_recognition_failure",
                           None)
            self._process_grammar_callback(func, results=results_obj)
            return

        # If the words argument was not "other" or "reject", then it is a
        # sequence of (word, rule_id) 2-tuples.
        words_rules = tuple(words)
        words = tuple(word for word, _ in words)

        # Call the grammar's general process_recognition method, if present.
        func = getattr(self.grammar, "process_recognition", None)
        if func:
            if not self._process_grammar_callback(func, words=words,
                                                  results=results_obj):
                # Return early if the method didn't return True or equiv.
                return

        # Iterate through this grammar's rules, attempting to decode each.
        # If successful, call that rule's method for processing the
        # recognition and return.
        s = state_.State(words_rules, self.grammar.rule_names, self.engine)
        for r in self.grammar.rules:
            if not (r.active and r.exported):
                continue
            s.initialize_decoding()
            for _ in r.decode(s):
                if s.finished():
                    try:
                        root = s.build_parse_tree()

                        # Notify observers using the manager *before*
                        # processing.
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
