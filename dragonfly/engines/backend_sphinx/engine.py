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
Engine class for CMU Pocket Sphinx
"""

import contextlib
import logging
import os
import time
import wave

from threading import Timer, RLock, current_thread

from jsgf import GrammarError, RootGrammar, PublicRule, Literal
from pyaudio import PyAudio

from dragonfly import Grammar, Window
from dragonfly.engines.backend_sphinx import is_engine_available
from dragonfly.engines.backend_sphinx.grammar_wrapper import GrammarWrapper,\
    ProcessingState
from dragonfly.engines.backend_sphinx.training import TrainingDataWriter
from dragonfly2jsgf import Translator

from .compiler import SphinxJSGFCompiler
from .dictation import SphinxDictationContainer
from .recobs import SphinxRecObsManager
from ..base import EngineBase, EngineError, MimicFailure

try:
    from sphinxwrapper import *
except ImportError:
    # This is checked again in is_engine_available(). It's done here purely for
    # readability:
    # e.g. using PocketSphinx instead of sphinxwrapper.PocketSphinx
    pass


class UnknownWordError(Exception):
    pass


class SphinxEngine(EngineBase):
    """Speech recognition engine back-end for CMU Pocket Sphinx."""

    _name = "sphinx"
    DictationContainer = SphinxDictationContainer

    # A hypothesis from Pocket Sphinx can be None, so this object used to indicate
    # when a dictation hypothesis has not been calculated for the current utterance.
    _DICTATION_HYP_UNSET = object()

    def __init__(self):
        EngineBase.__init__(self)

        # Set up the engine logger
        logging.basicConfig()

        try:
            import sphinxwrapper
        except ImportError:
            self._log.error("%s: failed to import sphinxwrapper module." % self)
            raise EngineError("Failed to import the sphinxwrapper module.")

        # Import and set the default configuration module. This can be changed later
        # using the config property.
        from . import config
        self._config = None
        self.config = config

        # Set other variables
        self._decoder = None
        self._audio_buffers = []
        self.compiler = SphinxJSGFCompiler()
        self._recognition_observer_manager = SphinxRecObsManager(self)
        self._in_progress_states = set()
        self._current_grammar_wrapper = None
        self._keyphrase_thresholds = {}
        self._keyphrase_functions = {}

        # Set up keyphrase search names and valid search names for grammars.
        self._keyphrase_search_names = {"_key_phrases", "_wake_phrase"}
        self._valid_searches = set()

        # Members used in recognition timeouts
        self._last_recognition_time = None
        self._timeout_timer = None
        self._thread_lock = RLock()

        # Recognising loop control variables
        self._recognising = False
        self._cancel_recognition_next_time = False
        self._last_recognition_time = None

        # Variable used in caching dictation hypotheses for speech utterances.
        self._current_dictation_hyp = self._DICTATION_HYP_UNSET

        # Training data writer, initialised on connect().
        self._training_data_writer = None

        # Variable used in training sessions.
        self._training_session_active = False

    @property
    def config(self):
        """
        Python module/object containing engine configuration.

        Setting this property will raise an :class:`EngineError` if the given
        configuration object doesn't define each configuration option.

        You will need to restart the engine with :meth:`disconnect` and
        :meth:`connect` if you have made configuration changes with this property
        after :meth:`connect` has been called.

        :raises: EngineError
        :returns: config module/object
        """
        return self._config

    @config.setter
    def config(self, value):
        # Validate configuration module
        self.validate_config(value)
        self._config = value

    @staticmethod
    def validate_config(engine_config):
        attributes = [
            "DECODER_CONFIG", "PYAUDIO_STREAM_KEYWORD_ARGS", "LANGUAGE",
            "NEXT_PART_TIMEOUT", "START_ASLEEP", "WAKE_PHRASE",
            "WAKE_PHRASE_THRESHOLD", "SLEEP_PHRASE", "SLEEP_PHRASE_THRESHOLD",
            "TRAINING_DATA_DIR", "START_TRAINING_PHRASE",
            "START_TRAINING_THRESHOLD", "END_TRAINING_PHRASE",
            "END_TRAINING_THRESHOLD"
        ]
        not_preset = []
        for attr in attributes:
            if not hasattr(engine_config, attr):
                not_preset.append(attr)

        if not_preset:
            # Raise an error with the attributes that weren't set.
            not_preset.sort()
            raise EngineError("invalid engine configuration. The following "
                              "attributes were not present: %s"
                              % ", ".join(not_preset))

    @property
    def observer_manager(self):
        return self._recognition_observer_manager

    @property
    def log(self):
        return self._log

    def connect(self):
        """
        Set up the CMU Pocket Sphinx decoder.

        This method does nothing if the engine is already connected.
        """
        if self._decoder:
            return

        # Check that no search argument other than -lm is specified, as the
        # engine will be handling that side of things.
        decoder_config = self.config.DECODER_CONFIG
        search_args = search_arguments_set(decoder_config)

        # Note: len(search_args) > 1 is handled by sphinxwrapper internally by
        # raising an error, so we don't need handle that here.
        if len(search_args) == 1 and search_args[0] != "-lm":
            raise EngineError("invalid PS configuration: please do not specify "
                              "'%s' in the Config object" % search_args[0])

        # Initialise a new decoder with the given configuration
        self._decoder = PocketSphinx(decoder_config)
        self._valid_searches.add(self.dictation_search_name)

        # Set up callback function wrappers
        def hypothesis(hyp):
            # Set speech to the hypothesis string or None if there isn't one
            speech = hyp.hypstr if hyp else None
            return self._hypothesis_callback(speech, False)

        def speech_start():
            return self._speech_start_callback(False)

        self._decoder.hypothesis_callback = hypothesis
        self._decoder.speech_start_callback = speech_start

        try:
            # Check that all words in configuration keyphrases are in the
            # pronunciation dictionary. An UnknownWordError will be raised if one
            # isn't.
            words = []
            words.extend(self.config.WAKE_PHRASE.split())
            words.extend(self.config.SLEEP_PHRASE.split())
            words.extend(self.config.START_TRAINING_PHRASE.split())
            words.extend(self.config.END_TRAINING_PHRASE.split())
            self._validate_words(words, "keyphrase")

            # Set up wake phrase search using the engine configuration.
            self._decoder.set_kws_list("_wake_phrase", {
                self.config.WAKE_PHRASE: self.config.WAKE_PHRASE_THRESHOLD
            })

            # Add the sleep keyphrase + threshold to call pause_recognition when
            # heard.
            self.set_keyphrase(
                self.config.SLEEP_PHRASE, self.config.SLEEP_PHRASE_THRESHOLD,
                self.pause_recognition
            )

            # Add the start/end training session phrases, thresholds and methods
            # to call when heard.
            self.set_keyphrase(
                self.config.START_TRAINING_PHRASE,
                self.config.START_TRAINING_THRESHOLD,
                self.start_training_session
            )
            self.set_keyphrase(
                self.config.END_TRAINING_PHRASE,
                self.config.END_TRAINING_THRESHOLD,
                self.end_training_session
            )
        except UnknownWordError as e:
            # Log the error about unknown words.
            self._log.error(e.message)

        # Initialise a TrainingDataWriter instance if specified.
        if self.config.TRAINING_DATA_DIR:
            # Get required audio configuration from the engine config.
            channels, sample_width, rate = (
                self.config.PYAUDIO_STREAM_KEYWORD_ARGS["channels"],
                PyAudio().get_sample_size(
                    self.config.PYAUDIO_STREAM_KEYWORD_ARGS["format"]
                ),
                self.config.PYAUDIO_STREAM_KEYWORD_ARGS["rate"],
            )
            self._training_data_writer = TrainingDataWriter(
                self.config.TRAINING_DATA_DIR, "training",
                channels, sample_width, rate
            )
        else:
            self._training_data_writer = None

    def _free_engine_resources(self):
        """
        Internal method for freeing the resources used by the engine.
        """
        # Cancel and free the timeout timer if it is active.
        self._cancel_and_free_timeout_timer()

        # Free the decoder and clear the audio buffer list
        self._decoder = None
        self._audio_buffers = []

        # Reset other variables
        self._cancel_recognition_next_time = False
        self._current_grammar_wrapper = None
        self._current_dictation_hyp = self._DICTATION_HYP_UNSET
        self._training_session_active = False

        # Close the training data files and discard the writer if necessary.
        if self._training_data_writer:
            self._training_data_writer.close_files()
            self._training_data_writer = None

        # Clear dictionaries and sets
        self._grammar_wrappers.clear()
        self._in_progress_states.clear()
        self._valid_searches.clear()
        self._keyphrase_thresholds.clear()
        self._keyphrase_functions.clear()

    def disconnect(self):
        """
        Deallocate the CMU Sphinx decoder and any other resources used by it.

        This method effectively unloads all loaded grammars and key phrases.
        """
        # Free resources if the decoder isn't currently being used to recognise,
        # otherwise stop the recognising loop, which will free the resources safely.
        if not self.recognising:
            self._free_engine_resources()
        else:
            self._recognising = False

    # -----------------------------------------------------------------------
    # Methods for working with grammars.

    def check_valid_word(self, word):
        """
        Check if a word is in the current Sphinx pronunciation dictionary.

        This will always return False if :meth:`connect` hasn't been called.

        :rtype: bool
        """
        if self._decoder:
            return bool(self._decoder.lookup_word(word))

        return False

    def _validate_words(self, words, search_type):
        unknown_words = []

        # Use 'set' to de-duplicate the 'words' list.
        for word in set(words):
            if not self.check_valid_word(word):
                unknown_words.append(word)

        if unknown_words:
            # Sort the word list before using it.
            unknown_words.sort()
            raise UnknownWordError("%s used words not found in the pronunciation "
                                   "dictionary: %s"
                                   % (search_type, ", ".join(unknown_words)))

    def _build_grammar_wrapper(self, grammar):
        return GrammarWrapper(grammar, self)

    def set_grammar(self, wrapper):
        # Set and/or switch to an appropriate Pocket Sphinx search for a given
        # GrammarWrapper.
        # This method is thread safe.
        with self._thread_lock:
            self._set_grammar(wrapper)

    def _set_grammar(self, wrapper):
        self._current_grammar_wrapper = wrapper

        # Return if the engine isn't available or if wrapper is None.
        if not (is_engine_available() and wrapper):
            return

        # Connect to the engine if it isn't connected already.
        self.connect()

        # Don't allow grammar wrappers to use key phrase search names.
        if wrapper.search_name in self._keyphrase_search_names:
            raise EngineError("grammar cannot use '%s' as a search name"
                              % wrapper.search_name)

        # Check if the wrapper's search_name is valid
        if wrapper.search_name in self._valid_searches:
            # If the wrapper's search_name is not the active search name, then swap
            # to it.
            if wrapper.search_name != self._decoder.active_search:
                self._decoder.end_utterance()
                self._decoder.active_search = wrapper.search_name

            # wrapper.search_name is active and is a valid search, so return.
            return

        # Compile and set the jsgf search. If it compiles to nothing or if there is
        # a GrammarError during compilation, fallback to the dictation search
        # instead.
        try:
            compiled = wrapper.dictation_grammar.compile_as_root_grammar()
            if "<root>" not in compiled:
                compiled = ""
        except GrammarError:
            compiled = ""

        if compiled:
            try:
                # Check that each word in the grammar is in the pronunciation
                # dictionary. This will raise an UnknownWordError if one or more
                # aren't.
                self._validate_words(wrapper.grammar_words,
                                     "grammar '%s'" % wrapper.grammar.name)

                # Set the JSGF search
                self._decoder.end_utterance()
                self._decoder.set_jsgf_string(wrapper.search_name, compiled)
                self._decoder.active_search = wrapper.search_name
            except RuntimeError:
                self._log.error("error setting PS JSGF search: %s" % compiled)

                # Return early to avoid adding this search as valid.
                return
        else:
            self._set_dictation_search()

        # Grammar search has been loaded, add the search name to the set.
        self._valid_searches.add(self._decoder.active_search)

    def unset_search(self, name):
        # Unset a Pocket Sphinx search with the given name.
        # Note that this method will not unset the dictation or keyphrase searches.
        # This method is thread safe.
        with self._thread_lock:
            if (name == self.dictation_search_name or
                    name in self._keyphrase_search_names):
                return

            if name in self._valid_searches:
                # TODO Unset the Pocket Sphinx search.
                # Unfortunately, the C function for doing this (ps_unset_search) is
                # not exposed... >_<
                # With the current Python API, this could be done either by freeing
                # the decoder used or by overriding the Pocket Sphinx search with
                # something else.

                # Remove the search from the valid searches set.
                self._valid_searches.remove(name)

    # TODO Add optional context parameter
    def set_keyphrase(self, keyphrase, threshold, func):
        """
        Add a keyphrase to listen for.

        Key phrases take precedence over grammars as they are processed first.
        They cannot be set for specific contexts (yet).

        :param keyphrase: keyphrase to add.
        :param threshold: keyphrase threshold value to use.
        :param func: function or method to call when the keyphrase is heard.
        :type keyphrase: str
        :type threshold: float
        :type func: callable
        """
        # Check that all words in the keyphrase are in the pronunciation dictionary.
        try:
            self._validate_words(keyphrase.split(), "keyphrase")
        except UnknownWordError as e:
            # Log an error and return early.
            self._log.error(e.message)
            return

        # Add parameters to the relevant dictionaries.
        self._keyphrase_thresholds[keyphrase] = threshold
        self._keyphrase_functions[keyphrase] = func

        # Set the keyphrase search (again)
        self._decoder.end_utterance()
        self._decoder.set_kws_list("_key_phrases", self._keyphrase_thresholds)

    def unset_keyphrase(self, keyphrase):
        """
        Remove a set keyphrase so that the engine no longer listens for it.

        :param keyphrase: keyphrase to remove.
        :type keyphrase: str
        """
        # Remove parameters from the relevant dictionaries. Don't raise an error
        # if there is no such keyphrase.
        self._keyphrase_thresholds.pop(keyphrase, None)
        self._keyphrase_functions.pop(keyphrase, None)

        # Set the keyphrase search (again)
        self._decoder.end_utterance()
        self._decoder.set_kws_list("_key_phrases", self._keyphrase_thresholds)

    def _set_dictation_search(self):
        # Change the active search to the one used for recognising dictation.
        if not self.recognising_dictation:
            self._decoder.end_utterance()  # ensure we're not processing
            self._decoder.active_search = "_default"

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

        wrapper = self._build_grammar_wrapper(grammar)
        try:
            self.set_grammar(wrapper)
        except UnknownWordError as e:
            # Unknown words should be logged as plain error messages, not
            # exception stack traces.
            self._log.error(e.message)
        except Exception as e:
            self._log.exception("Failed to load grammar %s: %s."
                                % (grammar, e))
        return wrapper

    def _unload_grammar(self, grammar, wrapper):
        try:
            # Unload the current and default searches for the grammar.
            # It doesn't matter if the names are the same.
            self.unset_search(wrapper.search_name)
            self.unset_search(wrapper.default_search_name)
        except Exception as e:
            self._log.exception("Failed to unload grammar %s: %s."
                                % (grammar, e))

    def set_exclusiveness(self, grammar, exclusive):
        try:
            # Not sure what this is, just going to silently ignore it for now
            self._log.debug("set_exclusiveness called for grammar %s. Not doing "
                            "anything yet.")
        except Exception as e:
            self._log.exception("Engine %s: failed set exclusiveness: %s."
                                % (self, e))

    def activate_grammar(self, grammar):
        self._log.debug("Activating grammar %s." % grammar.name)
        grammar.enable()

    def deactivate_grammar(self, grammar):
        self._log.debug("Deactivating grammar %s." % grammar.name)
        grammar.disable()

    def activate_rule(self, rule, grammar):
        self._log.debug("Activating rule %s in grammar %s." % (rule.name, grammar.name))
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return
        try:
            wrapper.dictation_grammar.enable_rule(rule.name)
            self.unset_search(wrapper.search_name)
            self.set_grammar(wrapper)
        except Exception as e:
            self._log.exception("Failed to activate grammar %s: %s."
                                % (grammar, e))

    def deactivate_rule(self, rule, grammar):
        self._log.debug("Deactivating rule %s in grammar %s." % (rule.name, grammar.name))
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return
        try:
            wrapper.dictation_grammar.disable_rule(rule.name)
            self.unset_search(wrapper.search_name)
            self.set_grammar(wrapper)
        except Exception as e:
            self._log.exception("Failed to activate grammar %s: %s."
                                % (grammar, e))

    def update_list(self, lst, grammar):
        wrapper = self._get_grammar_wrapper(grammar)
        name = lst.name
        if not wrapper:
            return

        assert isinstance(wrapper, GrammarWrapper)

        # Unfortunately there is no way to update lists for Pocket Sphinx without
        # reloading the grammar, so we'll update the list's JSGF rule and reload.

        # Rebuild the list's JSGF rule using dragonfly2jsgf's Translator class
        new_rule = Translator.translate_list(lst)

        # Find the old list rule in the grammar and modify its expansion
        for r in wrapper.dictation_grammar.rules:
            if r.name == name:
                r.expansion.children = new_rule.expansion.children
                break

        # Reload the grammar's Pocket Sphinx JSGF searches.
        self.unset_search(wrapper.search_name)
        self.unset_search(wrapper.default_search_name)
        self.set_grammar(wrapper)

    # -----------------------------------------------------------------------
    # Miscellaneous methods.

    @property
    def recognising(self):
        """
        Whether the engine is recognising speech in a loop.

        To stop recognition, use :meth:`disconnect`.

        :rtype: bool
        """
        return self._recognising

    @property
    def dictation_search_name(self):
        # The name of the Pocket Sphinx search used for processing speech as
        # dictation.
        return "_default"

    @property
    def recognising_dictation(self):
        # Return whether the engine is currently processing speech as dictation.
        return self._decoder.active_search == self.dictation_search_name

    def get_dictation_hypothesis(self):
        # Get a dictation hypothesis by reprocessing the audio buffers.

        # This method will calculate the dictation hypothesis once and use the same
        # value for successive calls in the processing of a speech utterance.
        if self._current_dictation_hyp is not self._DICTATION_HYP_UNSET:
            return self._current_dictation_hyp

        # Save the current Pocket Sphinx search
        current_search = self._decoder.active_search

        # Switch to the dictation search and reprocess the audio buffers.
        self._set_dictation_search()
        dict_hypothesis = self._decoder.batch_process(self._audio_buffers,
                                                      use_callbacks=False)
        if dict_hypothesis:
            dict_hypothesis = dict_hypothesis.hypstr

        # Switch back to the last search
        if current_search != self._decoder.active_search:
            self._decoder.active_search = current_search

        # Set _current_dictation_hyp
        self._current_dictation_hyp = dict_hypothesis
        return dict_hypothesis

    def _clear_in_progress_states_and_reset(self):
        # While holding the thread lock, clear in-progress states and reset
        # grammar wrappers. This is required as the in-progress state set is
        # a shared resource. This should make the method thread safe.
        with self._thread_lock:
            for wrapper in self._grammar_wrappers.values():
                wrapper.reset_all_sequence_rules()
            self._in_progress_states.clear()

    def _cancel_and_free_timeout_timer(self):
        """
        Cancel and free the timer used for recognition timeouts.
        """
        if not self._timeout_timer:
            return

        # This cannot be done from the Timer thread.
        if current_thread() is self._timeout_timer:
            return

        # Cancel the timer.
        self._timeout_timer.cancel()

        # If the timer is alive, call join on it, timing out after 100ms to prevent
        # deadlocks.
        if self._timeout_timer.isAlive():
            self._timeout_timer.join(0.1)

        # Free it - Timer objects cannot be reused.
        self._timeout_timer = None

    def _on_next_part_timeout(self):
        """
        Method called when there is a next rule part timeout.
        """
        # Do nothing if the timeout value is 0.
        if not self.config.NEXT_PART_TIMEOUT:
            return

        # Execute the following while holding _thread_lock to prevent race
        # conditions, such as the _in_progress_states set changing during
        # iteration and raising an error.
        with self._thread_lock:
            current_time = time.time()
            self._log.info("Recognition time-out after %f seconds"
                           % (current_time - self._last_recognition_time))

            # Remove any states with out of context grammars.
            fg_window = Window.get_foreground()
            for state in tuple(self._in_progress_states):
                # Do context checking for each state.
                state.wrapper.process_begin(fg_window)

                # Remove the state if the grammar is not active.
                if not state.wrapper.grammar_active:
                    self._in_progress_states.remove(state)

            # Calculate the best in-progress state with complete rules if there is
            # one.
            best_state = self._get_best_processing_state(
                [s for s in self._in_progress_states if s.complete_rules]
            )

            if best_state and best_state.wrapper.grammar_active:
                best_state.process(
                    timed_out=True,
                    notify_only=self._training_session_active
                )

            self._clear_in_progress_states_and_reset()

    def _handle_recognition_timeout(self):
        """
        Internal method for handling recognition timeouts. If a recognition timeout
        has not occurred yet, this method will cancel any scheduled timeout.

        The timeout period is specific to rules containing Dictation elements which
        must be recognised in sequence, although if there are matching normal rules,
        those will be processed on timeout.
        """
        next_part_timeout = self.config.NEXT_PART_TIMEOUT
        current_time = time.time()
        if not self._last_recognition_time:
            timed_out = False
        else:
            timed_out = next_part_timeout and (
                current_time >= self._last_recognition_time + next_part_timeout
            )

        if not timed_out:
            # If there is a timer, cancel and free it.
            # It is important that this is not called while holding the lock as
            # a deadlock can occur.
            if self._timeout_timer:
                self._cancel_and_free_timeout_timer()
        else:
            self._clear_in_progress_states_and_reset()

    def _get_best_processing_state(self, states):
        """
        Internal method to get the best ProcessingState object from a list of
        states.

        :type states: list
        :return: ProcessingState
        """
        # Filter out any states that are not processable.
        states = [s for s in states if s.is_processable]
        if not states:
            return None  # no best processing state

        final_states = None

        # Filter the states in 3 ways: states with matching normal rules, states
        # with matching and complete sequence rules, and states with in-progress
        # rules.
        complete_normal = [s for s in states if s.complete_normal_rules]
        complete_seq = [s for s in states if s.complete_sequence_rules]
        in_progress = [s for s in states if s.in_progress_rules]

        # Handle states with complete sequence rules first.
        if complete_seq and self._in_progress_states:
            # Set the final_states list
            final_states = complete_seq

        elif complete_seq and not self._in_progress_states:
            # Set the final_states list
            final_states = complete_seq + complete_normal

        # Then states with matching in-progress rules.
        elif in_progress and not self._in_progress_states:
            # Add states with in-progress and complete normal rules to the engine's
            # set. Complete normal rules should be added in case a next rule part
            # timeout occurs, where they will be processed, if the grammar is still
            # in-context and loaded.
            for state in in_progress:
                self._in_progress_states.add(state)
            for state in complete_normal:
                self._in_progress_states.add(state)

            # Set the final_states list
            final_states = in_progress + complete_normal

        elif in_progress:
            # Replace the old in-progress states with the new ones.
            self._in_progress_states = set(in_progress)

            # Set the final_states list
            final_states = in_progress

        # Then states with only normal matching rules.
        elif complete_normal:
            # Set the final_states list
            final_states = complete_normal

        if final_states:
            # Do any post collection tasks for all states.
            for state in states:
                state.do_post_collection_tasks()

            # Sort the list by the best state to use and return the first state.
            final_states.sort()
            return final_states[0]
        else:
            # Otherwise return None (no best state).
            return None

    def _get_best_hypothesis(self, hypothesises):
        """
        Take a list of speech hypothesises and return the most likely one.

        :type hypothesises: iterable
        :return: str | None
        """
        # Get all distinct, non-null hypothesises using a set and a filter.
        distinct = tuple([h for h in set(hypothesises) if bool(h)])
        if not distinct:
            return None
        elif len(distinct) == 1:
            return distinct[0]  # only one choice

        # Decide between non-null hypothesises using a Pocket Sphinx search with
        # each hypothesis as a grammar rule.
        grammar = RootGrammar()
        grammar.language_name = self.language
        for i, hypothesis in enumerate(distinct):
            grammar.add_rule(PublicRule("rule%d" % i, Literal(hypothesis)))

        compiled = grammar.compile_as_root_grammar()
        name = "_temp"

        # Store the current search name.
        original = self._decoder.active_search

        # Note that there is no need to validate words in this case because each
        # literal in the _temp grammar came from a Pocket Sphinx hypothesis.
        self._decoder.end_utterance()
        self._decoder.set_jsgf_string(name, compiled)
        self._decoder.active_search = name

        # Do the processing.
        result = self._decoder.batch_process(
            self._audio_buffers,
            use_callbacks=False
        )

        # Switch back to the previous search.
        self._decoder.end_utterance()  # just in case
        self._decoder.active_search = original

        if result:
            result = result.hypstr
        return result

    def _set_current_grammar_search(self):
        # Set _current_grammar_wrapper and the active search to the search of an
        # active grammar. If there is no active grammar, set current wrapper to None
        # and active search to the dictation search.
        active_wrappers = list(filter(
            lambda w: w.grammar_active,
            self._grammar_wrappers.values()
        ))
        if active_wrappers:
            # Switch to the first active grammar wrapper's search.
            self._current_grammar_wrapper = active_wrappers[0]
            self.set_grammar(self._current_grammar_wrapper)
        else:
            # No wrapper is usable. Set the dictation search.
            self._current_grammar_wrapper = None
            self._set_dictation_search()

    def _speech_start_callback(self, mimicking):
        # Get context info. Dragonfly has a handy static method for this:
        fg_window = Window.get_foreground()

        # Call process_begin for all grammars so that any out of context grammar
        # will not be used.
        for wrapper in self._grammar_wrappers.values():
            wrapper.process_begin(fg_window)

        # If there are any in-progress states whose grammars are out of context,
        # remove them from the set. Do this while holding the lock to prevent race
        # conditions; the timeout timer could be active at this point.
        with self._thread_lock:
            for state in tuple(self._in_progress_states):
                assert isinstance(state, ProcessingState)
                if not state.wrapper.grammar_active:
                    self._in_progress_states.remove(state)
                    state.wrapper.reset_all_sequence_rules()

        # Handle recognition timeout where speech started too late
        self._handle_recognition_timeout()

        # Set a new current grammar wrapper if necessary.
        if (not self._current_grammar_wrapper or
                not self._current_grammar_wrapper.grammar_active):
            self._set_current_grammar_search()

        # Do a few things with audio buffers if not mimicking.
        if not mimicking:
            # Reprocess current audio buffers if necessary; <decoder>.end_utterance
            # can be called by the above code or by the timer thread.
            if self._decoder.utt_ended and not mimicking:
                self._decoder.batch_process(self._audio_buffers, use_callbacks=False)

            # Trim excess audio buffers from the start of the list. Keep a maximum 3
            # seconds of silence before speech start was detected. This should help
            # increase the performance of batch reprocessing later.
            chunk = self.config.PYAUDIO_STREAM_KEYWORD_ARGS["frames_per_buffer"]
            rate = self.config.PYAUDIO_STREAM_KEYWORD_ARGS["rate"]
            seconds = 3
            n_buffers = int(rate / chunk * seconds)
            self._audio_buffers = self._audio_buffers[-1 * n_buffers:]

            # Add trimmed pre-speech audio buffers to training .wav file.
            if self._training_data_writer:
                for buf in self._audio_buffers:
                    self._training_data_writer.write_to_wave_file(buf)

        # Notify observers
        self.observer_manager.notify_begin()

    def _hypothesis_callback(self, speech, mimicking):
        """
        Internal Pocket Sphinx hypothesis callback method. Calls _process_hypothesis
        and does post-processing afterwards.
        :param speech: hypothesis string | None
        :param mimicking:  whether to treat speech as mimicked speech.
        :rtype: bool
        """
        # Process speech. We should get back a boolean for whether processing
        # occurred as well as the final speech hypothesis.
        processing_occurred, speech = self._process_hypothesises(
            speech, mimicking
        )

        # Do some things that should be done if no processing occurred.
        if not processing_occurred:
            self.observer_manager.notify_failure()
            self._clear_in_progress_states_and_reset()
            self._cancel_and_free_timeout_timer()
            self.set_grammar(self._current_grammar_wrapper)

        # Finalise the current training data and open a new wav file. If speech is
        # None, the current .wav file will be discarded.
        if self._training_data_writer and not mimicking:
            self._training_data_writer.finalise(speech)
            self._training_data_writer.open_next_wav_file()

        # Clear the internal audio buffer list because it is no longer needed.
        self._audio_buffers = []

        # Unset the dictation hypothesis because it is now invalid.
        self._current_dictation_hyp = self._DICTATION_HYP_UNSET

        # Return whether processing occurred in case this method was called by
        # mimic.
        return processing_occurred

    def _process_key_phrases(self, speech, mimicking):
        """
        Processing key phrase searches and return the matched keyphrase (if any).

        :type speech: str
        :param mimicking: whether to treat speech as mimicked speech.
        :rtype: str
        """
        key_phrases_search = "_key_phrases"
        if (self._decoder.active_search == key_phrases_search
                and not speech or not speech and mimicking):
            return None  # no matches

        if self._decoder.active_search != key_phrases_search and not mimicking:
            # End the utterance if it isn't already ended.
            self._decoder.end_utterance()

            # Reprocess using the key phrases search
            last = self._decoder.active_search
            self._decoder.active_search = key_phrases_search
            hyp = self._decoder.batch_process(self._audio_buffers,
                                              use_callbacks=False)

            # Get the hypothesis string.
            speech = hyp.hypstr if hyp else None

            # Restore last search.
            self._decoder.end_utterance()
            self._decoder.active_search = last

        if not speech:
            return None

        # Handle multiple matching key phrases. This appears to be a quirk of how
        # Pocket Sphinx 'kws' searches work. Get the best match instead if this is
        # the case.
        recognised_phrases = speech.split("  ")
        if len(recognised_phrases) > 1:
            # Remove trailing space from the last phrase.
            recognised_phrases[len(recognised_phrases) - 1].rstrip()
            speech = self._get_best_hypothesis(recognised_phrases)
        else:
            speech = speech.rstrip()  # remove trailing whitespace.

        # Call the registered function if there was a match and the function
        # is callable.
        func = self._keyphrase_functions.get(speech, None)
        if callable(func):
            func()

        # Return speech if it matched a keyphrase.
        result = speech if speech in self._keyphrase_functions else None
        return result

    def _process_hypothesises(self, speech, mimicking):
        """
        Internal method to process speech hypothesises. This should only be called
        from 'SphinxEngine._hypothesis_callback' because that method does important
        post processing.

        :type speech: str
        :param mimicking: whether to treat speech as mimicked speech.
        :rtype: tuple
        """
        # Check key phrases search first.
        keyphrase = self._process_key_phrases(speech, mimicking)
        if keyphrase:
            # Keyphrase search matched. Notify observers and return True.
            words_list = [(word, 0) for word in keyphrase.split()]
            self.observer_manager.notify_recognition(words_list)
            return True, keyphrase

        # Otherwise do grammar processing.
        processing_occurred = False
        hypothesises = {}

        # If the engine is processing in-progress rules, only use active in-progress
        # wrappers.
        in_progress_states = self._in_progress_states
        if in_progress_states:
            wrappers = [s.wrapper for s in in_progress_states
                        if s.wrapper.grammar_active]

        # Otherwise collect each active grammar's GrammarWrapper.
        else:
            wrappers = [w for w in self._grammar_wrappers.values()
                        if w.grammar_active]

        self._last_recognition_time = time.time()

        # No grammar has been loaded.
        if not self._current_grammar_wrapper or not wrappers:
            # TODO What should we do here? Output formatted Dictation like DNS?
            return processing_occurred, speech

        if (self._current_grammar_wrapper.search_name !=
                self._decoder.active_search):
            # The grammar's search isn't set, so reprocess speech.
            self.set_grammar(self._current_grammar_wrapper)

            if not mimicking:
                hyp = self._decoder.batch_process(
                    self._audio_buffers,
                    use_callbacks=False
                )
                if hyp and not isinstance(hyp, str):
                    speech = hyp.hypstr
                else:
                    speech = hyp

        if mimicking == "as words":
            # Set dictation hypothesis to None if mimicking with engine.mimic
            self._current_dictation_hyp = None
        elif mimicking:
            # Or if using mimic_phrases, use speech.
            self._current_dictation_hyp = speech

        # Use speech as the hypothesis for the current grammar wrapper.
        hypothesises[self._current_grammar_wrapper.search_name] = speech

        # Batch process audio buffers for each active grammar. Store each
        # hypothesis.
        for wrapper in wrappers:
            if mimicking:
                # Just use speech for every hypothesis if mimicking.
                hypothesises[wrapper.search_name] = speech
            elif wrapper.search_name not in hypothesises.keys():
                # Switch to the search for this grammar if necessary
                if self._decoder.active_search != wrapper.search_name:
                    self._decoder.active_search = wrapper.search_name

                # TODO Do this in parallel with multiple decoders and Python's multiprocessing package
                hypothesis = self._decoder.batch_process(
                    self._audio_buffers,
                    use_callbacks=False
                )

                if hypothesis:
                    hypothesis = hypothesis.hypstr

                hypothesises[wrapper.search_name] = hypothesis

        # Get the best hypothesis.
        speech = self._get_best_hypothesis(list(hypothesises.values()))

        # Only use wrappers whose search hypothesis is speech.
        wrappers = [w for w in wrappers if hypothesises[w.search_name] == speech]

        processing_states = []
        for wrapper in wrappers:
            # Collect matching rules in a ProcessingState object for each
            # wrapper
            hyp = hypothesises[wrapper.search_name]

            # If called by engine.mimic (not engine.mimic_phrases), we need to match
            # on LinkedRules instead to get a complete match, especially if there's
            # dictation involved.
            if mimicking == "as words":
                processing_states.append(ProcessingState(wrapper, hyp, True))
            else:
                processing_states.append(ProcessingState(wrapper, hyp))

        # Process the best wrapper
        best_state = self._get_best_processing_state(processing_states)
        if best_state:
            best_state.process(notify_only=self._training_session_active)

            # TODO Handle complete sequence rules that can repeat.
            # if best_state.repeatable_complete_sequence_rules:
            #     # Start the repetition timeout timer.
            #     pass
            if best_state.complete_sequence_rules:
                # Now that a complete sequence rule has been processed,
                # clear the engine's in-progress set and reset all wrappers.
                self._clear_in_progress_states_and_reset()

            processing_occurred = True

        # If there are in-progress states, cancel the timer if it is running and
        # start the timer.
        timeout_value = self.config.NEXT_PART_TIMEOUT
        self._cancel_and_free_timeout_timer()
        if self._in_progress_states and timeout_value:
            # Start the timer.
            self._timeout_timer = Timer(
                timeout_value,
                self._on_next_part_timeout
            )
            self._timeout_timer.start()

        # Return whether processing occurred and the final speech hypothesis for
        # post processing.
        return processing_occurred, speech

    def process_buffer(self, buf, sleep_time=0.1):
        """
        Recognise speech from an audio buffer. This method is meant to be called
        in sequence for multiple buffers.

        :param buf: audio buffer
        :param sleep_time: time to sleep after processing an audio buffer. Use 0
            for no sleep time.
        :type sleep_time: float
        :type buf: str
        """
        # Cancel current recognition if it has been requested.
        if self._cancel_recognition_next_time:
            self._decoder.end_utterance()
            self._audio_buffers = []
            self._cancel_recognition_next_time = False

        # Keep a list of buffers for possible reprocessing using different Pocket
        # Sphinx searches later.
        self._audio_buffers.append(buf)

        # Write the buffer to the current .wav file used for acoustic model
        # training. Only do this if in speech, the writer is initialised and
        # recognition is not paused.
        if self._decoder.get_in_speech() and self._training_data_writer and \
                not self.recognition_paused:
            self._training_data_writer.write_to_wave_file(buf)

        # Process audio and wait a few milliseconds.
        self._decoder.process_audio(buf)

        # This improves the performance; we don't need to process as much audio
        # as the device can read, and people don't speak that fast anyway!
        time.sleep(sleep_time)

    def process_wave_file(self, path):
        """
        Recognise speech from a wave file. This method checks that the wave file is
        valid. It raises an error if the file doesn't exist, if it can't be read or
        if the WAV header values do not match those in the engine configuration.

        The wave file must use the same sample width, sample rate and number of
        channels defined in the engine configuration ``PYAUDIO_STREAM_KEYWORD_ARGS``
        attribute.

        If the file is valid, :meth:`process_buffer` is then used to process
        the audio.

        :param path: wave file path
        :raises: IOError | OSError | ValueError
        """
        if not self._decoder:
            self.connect()

        # This method's implementation has been adapted from the PyAudio play wave
        # example: http://people.csail.mit.edu/hubert/pyaudio/#play-wave-example

        # Check that path is a valid file.
        if not os.path.isfile(path):
            raise IOError("'%s' is not a file. Please use a different file path.")

        # Get required audio configuration from the engine config.
        p = PyAudio()
        channels, sample_width, rate, chunk = (
            self.config.PYAUDIO_STREAM_KEYWORD_ARGS["channels"],
            p.get_sample_size(
                self.config.PYAUDIO_STREAM_KEYWORD_ARGS["format"]
            ),
            self.config.PYAUDIO_STREAM_KEYWORD_ARGS["rate"],
            self.config.PYAUDIO_STREAM_KEYWORD_ARGS["frames_per_buffer"]
        )

        # Open the wave file. Use contextlib to make sure that the file is closed
        # whether errors are raised or not.
        with contextlib.closing(wave.open(path, "rb")) as wf:
            # Validate the wave file's header.
            if wf.getnchannels() != channels:
                raise ValueError("WAV file '%s' should use %d channel(s), not %d!"
                                 % (path, channels, wf.getnchannels()))
            elif wf.getsampwidth() != sample_width:
                raise ValueError("WAV file '%s' should use sample width %d, not %d!"
                                 % (path, sample_width, wf.getsampwidth()))
            elif wf.getframerate() != rate:
                raise ValueError("WAV file '%s' should use sample rate %d, not %d!"
                                 % (path, rate, wf.getframerate()))

            # Use process_buffer to process each buffer.
            data = wf.readframes(chunk)
            while data != "":
                self.process_buffer(data, 0)  # no sleep time required
                data = wf.readframes(chunk)

    def post_loader_init(self):
        """
        Do post grammar loader initialisation tasks that can't be done in
        :meth:`connect`.

        This is automatically called by :meth:`recognise_forever`, but **not** by
        :meth:`process_buffer` or :meth:`process_wave_file`.

        This currently only handles the engine's ``START_ASLEEP`` configuration
        option.
        """
        # Start in sleep mode if requested.
        if self.config.START_ASLEEP:
            self.pause_recognition()
            self.log.info("Starting in sleep mode as requested.")

    def recognise_forever(self):
        """
        Start recognising from the default recording device until
        :meth:`disconnect` is called.

        Recognition can be paused and resumed using either the sleep/wake key
        phrases or by calling :meth:`pause_recognition` or
        :meth:`resume_recognition`.

        To configure audio input settings, modify the engine's
        ``PYAUDIO_STREAM_KEYWORD_ARGS`` configuration attribute.
        """
        # Open a PyAudio stream with the specified keyword args and get the number
        # of frames to read per buffer
        p = PyAudio()
        keyword_args = self.config.PYAUDIO_STREAM_KEYWORD_ARGS
        stream = p.open(**keyword_args)
        frames_per_buffer = keyword_args["frames_per_buffer"]

        # Do post grammar loader initialisation.
        self.post_loader_init()

        # Start recognising in a loop
        stream.start_stream()
        self._recognising = True
        self._cancel_recognition_next_time = False
        while self.recognising:
            # Read from the audio device (default number of frames is 2048)
            self.process_buffer(stream.read(frames_per_buffer))

        stream.close()
        self._free_engine_resources()

    def mimic(self, words):
        """ Mimic a recognition of the given *words* """
        if isinstance(words, (list, tuple)):
            words = " ".join(words)

        if self.recognition_paused:
            wake_phrase = self.config.WAKE_PHRASE.strip().lower()
            if words and words.strip().lower() == wake_phrase:
                # Resume if the wake phrase was mimicked.
                self.resume_recognition()

            # Silently return either way.
            return

        # Pretend that Sphinx has started processing speech
        self._speech_start_callback(True)

        # Process the words as if they were spoken
        result = self._hypothesis_callback(words, "as words")
        if not result:
            raise MimicFailure("No matching rule found for words %s." % words)

    def mimic_phrases(self, *phrases):
        """
        Mimic a recognition of the given *phrases*.

        This method accepts variable phrases instead of a list of words to allow
        mimicking of rules using :class:`Dictation` elements.
        """
        if self.recognition_paused:
            words = " ".join(phrases)
            self.mimic(words)  # delegate to mimic()
            return

        # Pretend that Sphinx has started processing speech
        self._speech_start_callback(True)

        # Process phrases as if they were spoken
        for phrase in phrases:
            result = self._hypothesis_callback(phrase, True)
            if not result:
                raise MimicFailure("No matching rule found for words %s."
                                   % phrase)

    def speak(self, text):
        # CMU Sphinx speech recognition engines don't come with text-to-speech
        # functionality. For those who need this, the Jasper project has
        # implementations for popular text-to-speech engines:
        # https://github.com/jasperproject/jasper-client
        raise NotImplementedError("text-to-speech is not implemented for this "
                                  "engine")

    def _get_language(self):
        return self.config.LANGUAGE

    # ---------------------------------------------------------------------
    # Training session methods

    def start_training_session(self):
        """
        Start the training session. This will stop recognition processing
        until either :meth:`end_training_session` is called or the end training
        keyphrase is heard.

        This method is thread safe.
        """
        with self._thread_lock:
            if not self._training_data_writer:
                self._log.warning(
                    "Training data will not be recorded! Please call "
                    "connect() and/or check that engine config "
                    "'TRAINING_DATA_DIR' is set to a valid path.")

            if not self._training_session_active:
                self._log.info("Training session has started. No rule "
                               "actions will be processed. ")
                self._log.info("Say '%s' to end the session."
                               % self.config.END_TRAINING_PHRASE)
                self._training_session_active = True

    def end_training_session(self):
        """
        End the training if one is in progress. This will allow recognition
        processing once again.

        This method is thread safe.
        """
        with self._thread_lock:
            if self._training_session_active:
                self._log.info("Ending training session. Rule actions "
                               "will now be processed normally again.")
                self._training_session_active = False

    # ---------------------------------------------------------------------
    # Recognition loop control methods
    # Stopping recognition loop is done using disconnect()

    @property
    def recognition_paused(self):
        """
        Whether the engine is waiting for the wake phrase to be heard or for
        :meth:`resume_recognition` to be called.

        This property returns False if :meth:`connect` hasn't been called yet.

        :rtype: bool
        """
        if self._decoder:
            return self._decoder.active_search == "_wake_phrase"
        return False

    def pause_recognition(self):
        """
        Pause recognition and wait for :meth:`resume_recognition` to be called or
        for the wake keyphrase to be spoken.

        This method is thread safe.
        """
        with self._thread_lock:
            if not self._decoder:
                return

            # Stop in-progress processing.
            self._clear_in_progress_states_and_reset()

            # Switch to the wake keyphrase search.
            self._decoder.end_utterance()
            self._decoder.active_search = "_wake_phrase"

            # Define temporary callback methods for the decoder.
            def speech_start():
                # Do nothing here for the moment. Another observer notify method
                # could be used if appropriate.
                pass

            def hypothesis(hyp):
                s = hyp.hypstr if hyp else None

                # Resume recognition if s is the wake keyphrase.
                if s and s.strip() == self.config.WAKE_PHRASE.strip():
                    self.resume_recognition()
                else:
                    self.log.debug("Didn't hear %s" % self.config.WAKE_PHRASE)

                # Clear audio buffers
                self._audio_buffers = []

            # Override decoder callback methods.
            self._decoder.speech_start_callback = speech_start
            self._decoder.hypothesis_callback = hypothesis

    def resume_recognition(self):
        """
        Resume listening for grammar rules and key phrases.

        This method is thread safe.
        """
        with self._thread_lock:
            if not self._decoder:
                return

            # Notify observers about recognition resume.
            keyphrase = self.config.WAKE_PHRASE
            words_list = [(word, 0) for word in keyphrase.strip().split()]
            self.observer_manager.notify_recognition(words_list)

            # Restore the callbacks to normal
            def speech_start():
                return self._speech_start_callback(False)

            def hypothesis(hyp):
                # Set speech to the hypothesis string or None if there isn't one
                speech = hyp.hypstr if hyp else None
                return self._hypothesis_callback(speech, False)

            self._decoder.hypothesis_callback = hypothesis
            self._decoder.speech_start_callback = speech_start

            # Switch to an active grammar search / dictation search.
            self._set_current_grammar_search()

    def cancel_recognition(self):
        """
        If a recognition was in progress, cancel it before processing the next
        audio buffer.

        This method is thread safe.
        """
        self._cancel_recognition_next_time = True
