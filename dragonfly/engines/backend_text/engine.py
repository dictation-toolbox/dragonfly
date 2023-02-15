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
from dragonfly.engines.backend_text.recobs   import TextRecObsManager
from dragonfly.windows.window                import Window


#---------------------------------------------------------------------------

class TextInputEngine(EngineBase):
    """Text-input Engine class. """

    _name = "text"
    DictationContainer = DictationContainerBase

    #-----------------------------------------------------------------------

    def __init__(self):
        EngineBase.__init__(self)
        self._language = "en"
        self._connected = False
        self._recognition_observer_manager = TextRecObsManager(self)
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
        return GrammarWrapper(grammar, self)

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
            command.  This is useful for testing context-specific commands.
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
            words = words.split()
        elif iter(words):
            words = [w for w in words]
        else:
            raise TypeError("%r is not a string or other iterable object"
                            % words)

        # Fail on empty input.
        if not words:
            raise MimicFailure("Invalid mimic input %r" % words)

        # Process the words as if they were spoken.  Pass along keyword
        #  arguments appropriately.
        self._emulate_start_speech(**kwargs)
        result = self._process_words(words)
        if not result:
            raise MimicFailure("No matching rule found for words %s."
                               % words)

    def _emulate_start_speech(self, **kwargs):
        # Get foreground window attributes.
        w = Window.get_foreground()
        window_info = {
            "executable": w.executable,
            "title": w.title,
            "handle": w.handle,
        }

        # Update *window_info* with keyword arguments passed to mimic().
        window_info.update(kwargs)

        # Call process_begin() for each grammar wrapper.
        # Note: A copy of_grammar_wrappers is used in case it changes.
        for wrapper in self._grammar_wrappers.copy().values():
            wrapper.begin_callback(**window_info)

    def _process_words(self, words):
        # Get a sequence of (word, rule_id) 2-tuples.
        words_rules = self._get_words_rules(words, 0)

        # Create a list of active grammars to process.
        # Include only active exclusive grammars if at least one is active.
        wrappers = []
        exclusive_count = 0
        for wrapper in self._grammar_wrappers.values():
            if wrapper.grammar_is_active: wrappers.append(wrapper)
            if wrapper.exclusive: exclusive_count += 1
        if exclusive_count > 0:
            wrappers = [w for w in wrappers if w.exclusive]

        # Initialize a *Results* object with information about this
        #  recognition.
        results = Results(words, False)

        # Attempt to process the words with the relevant grammars, stopping
        #  on the first one that processes them.
        result = False
        for wrapper in wrappers:
            rule_names = wrapper.grammar.rule_names
            result = wrapper.process_results(words_rules, rule_names,
                                             results, True)
            if result: break

        # If no processing has occurred, this is a recognition failure.
        if not result: self.dispatch_recognition_failure(results)

        # Return whether processing occurred.
        return result

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


#---------------------------------------------------------------------------

class GrammarWrapper(GrammarWrapperBase):

    # Enable guessing at which words were "dictated" so this back-end
    #  behaves like a real one.
    _dictated_word_guesses_enabled = True

    def __init__(self, grammar, engine):
        GrammarWrapperBase.__init__(self, grammar, engine)
        self.exclusive = False
    def _process_final_rule(self, state, words, results, dispatch_other,
                            rule, *args):
        # Recognition successful!  Set the results data.
        results.success = True
        results.rule = rule
        results.grammar = self.grammar

        # Call the base class method.
        GrammarWrapperBase._process_final_rule(self, state, words, results,
                                               dispatch_other, rule, *args)


#---------------------------------------------------------------------------

class Results(object):
    """ Text-input engine recognition results class. """

    def __init__(self, words, success):
        if isinstance(words, string_types):
            words = words.split()
        elif iter(words):
            words = [w for w in words]
        else:
            raise TypeError("%r is not a string or other iterable object"
                            % words)
        self._words = tuple(words)
        self._success = success
        self._grammar = None
        self._rule = None

    def words(self):
        """ Get the words for this recognition. """
        return self._words

    def _set_success(self, success):
        self._success = success

    recognition_success = property(lambda self: self._success, _set_success,
                                   doc="Whether this recognition has been"
                                       " processed successfully.")

    def _set_grammar(self, grammar):
        self._grammar = grammar

    grammar = property(lambda self: self._grammar, _set_grammar,
                       doc="The grammar which processed this recognition,"
                           " if any.")

    def _set_rule(self, rule):
        self._rule = rule

    rule = property(lambda self: self._rule, _set_rule,
                    doc="The rule that matched this recognition, if any.")
