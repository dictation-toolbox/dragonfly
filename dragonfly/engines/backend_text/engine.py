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

import sys
import time

from six                                     import string_types

import dragonfly.engines
from dragonfly.engines.base                  import (EngineBase,
                                                     MimicFailure,
                                                     ThreadedTimerManager,
                                                     DictationContainerBase,
                                                     GrammarWrapperBase)
from dragonfly.engines.backend_text.recobs   import TextRecobsManager
from dragonfly.windows.window                import Window


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

        """
        # The *words* argument should be a string or iterable.
        # Words are put into lowercase for consistency.
        if isinstance(words, string_types):
            words = words.lower().split()
        elif iter(words):
            words = [w.lower() for w in words]
        else:
            raise TypeError("%r is not a string or other iterable object"
                            % words)

        # Fail on empty input.
        if not words:
            raise MimicFailure("Invalid mimic input %r" % words)

        # Notify observers that a recognition has begun.
        self._recognition_observer_manager.notify_begin()

        # Get a sequence of (word, rule_id) 2-tuples.
        words_rules = self._get_words_rules(words, 0)

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
        # TODO Determine whether this should really be done for exclusive
        #  grammars.
        for wrapper in self._grammar_wrappers.copy().values():
            wrapper.process_begin(**process_args)

        # Take another copy of _grammar_wrappers to use for processing.
        grammar_wrappers = self._grammar_wrappers.copy().values()

        # Filter out inactive grammars.
        grammar_wrappers = [wrapper for wrapper in grammar_wrappers
                            if wrapper.grammar_is_active]

        # Include only exclusive grammars if at least one is active.
        exclusive_count = 0
        for wrapper in grammar_wrappers:
            if wrapper.exclusive: exclusive_count += 1
        if exclusive_count > 0:
            grammar_wrappers = [wrapper for wrapper in grammar_wrappers
                                if wrapper.exclusive]

        # Attempt to process the mimicked words, stopping on the first
        # grammar that processes them.
        result = False
        for wrapper in grammar_wrappers:
            rule_names = wrapper.grammar.rule_names
            result = wrapper.process_results(words_rules, rule_names, None)
            if result: break

        # If no processing has occurred, then the mimic has failed.
        if not result:
            self._recognition_observer_manager.notify_failure(None)
            raise MimicFailure("No matching rule found for words %r."
                               % (words,))

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        dragonfly.engines.get_speaker().speak(text)

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

    # Enable guessing at which words were "dictated" so that this "SR"
    #  back-end behaves like a real one.
    _dictated_word_guesses_enabled = True

    def __init__(self, grammar, engine, recobs_manager):
        GrammarWrapperBase.__init__(self, grammar, engine, recobs_manager)
        self.exclusive = False
