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
import locale
import os
import wave

from six import binary_type, text_type, string_types, PY2
from jsgf import RootGrammar, PublicRule, Literal
from sphinxwrapper import PocketSphinx

from dragonfly import Window
from ..base import (EngineBase, EngineError, MimicFailure,
                    DelegateTimerManagerInterface,
                    DictationContainerBase)
from .compiler import SphinxJSGFCompiler
from .grammar_wrapper import GrammarWrapper
from .misc import (EngineConfig, WaveRecognitionObserver,
                   get_decoder_config_object)
from .recobs import SphinxRecObsManager
from .recording import PyAudioRecorder
from .timer import SphinxTimerManager
from .training import write_training_data, write_transcript_files


class UnknownWordError(Exception):
    pass


def _map_to_str(text, encoding=locale.getpreferredencoding()):
    # Translate unicode/bytes to whatever str is in this version of
    # Python. Decoder methods seem to require str objects.
    if not isinstance(text, string_types):
        text = str(text)
    if PY2 and isinstance(text, text_type):
        text = text.encode(encoding)
    elif not PY2 and isinstance(text, binary_type):
        text = text.decode(encoding)
    return text


class SphinxEngine(EngineBase, DelegateTimerManagerInterface):
    """ Speech recognition engine back-end for CMU Pocket Sphinx. """

    _name = "sphinx"
    DictationContainer = DictationContainerBase

    def __init__(self):
        EngineBase.__init__(self)
        DelegateTimerManagerInterface.__init__(self)

        try:
            import sphinxwrapper, jsgf, pyaudio
        except ImportError as e:
            raise EngineError("Failed to import Pocket Sphinx engine "
                              "dependencies.")

        # Set the default engine configuration.
        # This can be changed later using the config property.
        self._config = None
        self.config = EngineConfig

        # Set other variables
        self._decoder = None
        self._audio_buffers = []
        self.compiler = SphinxJSGFCompiler(self)
        self._recognition_observer_manager = SphinxRecObsManager(self)
        self._keyphrase_thresholds = {}
        self._keyphrase_functions = {}
        self._training_session_active = False
        self._default_search_result = None
        self._grammar_count = 0

        # Timer-related members.
        self._timer_manager = SphinxTimerManager(0.02, self)

        # Set up keyphrase search names and valid search names for grammars.
        self._keyphrase_search_names = ["_key_phrases", "_wake_phrase"]
        self._valid_searches = set()

        # Recognising loop members.
        self._recorder = PyAudioRecorder(self.config)
        self._cancel_recognition_next_time = False
        self._recognising = False
        self._recognition_paused = False

    @property
    def config(self):
        """
        Python module/object containing engine configuration.

        You will need to restart the engine with :meth:`disconnect` and
        :meth:`connect` if the configuration has been changed after
        :meth:`connect` has been called.

        :returns: config module/object
        """
        return self._config

    @config.setter
    def config(self, value):
        # Validate configuration object.
        self.validate_config(value)
        self._config = value

    @classmethod
    def validate_config(cls, engine_config):
        # Check configuration options and set defaults where appropriate.
        # Set a new decoder config if necessary.
        if not hasattr(engine_config, "DECODER_CONFIG"):
            setattr(engine_config, "DECODER_CONFIG",
                    get_decoder_config_object())
        options = [
            "LANGUAGE",

            "START_ASLEEP",
            "WAKE_PHRASE",
            "WAKE_PHRASE_THRESHOLD",
            "SLEEP_PHRASE",
            "SLEEP_PHRASE_THRESHOLD",

            "TRAINING_DATA_DIR",
            "TRANSCRIPT_NAME",
            "START_TRAINING_PHRASE",
            "START_TRAINING_PHRASE_THRESHOLD",
            "END_TRAINING_PHRASE",
            "END_TRAINING_PHRASE_THRESHOLD",

            "CHANNELS",
            "RATE",
            "SAMPLE_WIDTH",
            "FRAMES_PER_BUFFER",
        ]

        # Get default values and set them they are missing.
        for option in options:
            if hasattr(engine_config, option):
                continue

            default_value = getattr(EngineConfig, option)
            if "PHRASE" in option:
                # Disable missing phrases by default if using a language
                # other than English.
                if not engine_config.LANGUAGE.startswith("en"):
                    default_value = "" if option.endswith("PHRASE") else 0.0
            setattr(engine_config, option, default_value)

    def connect(self):
        """
        Set up the CMU Pocket Sphinx decoder.

        This method does nothing if the engine is already connected.
        """
        if self._decoder:
            return

        # Initialise a new decoder with the given configuration
        decoder_config = self._config.DECODER_CONFIG
        self._decoder = PocketSphinx(decoder_config)
        self._valid_searches.add(self._default_search_name)

        # Set up callback function wrappers
        def hypothesis(hyp):
            # Set default search result.
            self._default_search_result = hyp

            # Set speech to the hypothesis string or None if there isn't one
            speech = hyp.hypstr if hyp else None
            return self._hypothesis_callback(speech, False)

        def speech_start():
            # Reset the default search result and call the engine's callback
            # method.
            self._default_search_result = None
            return self._speech_start_callback(False)

        self._decoder.hypothesis_callback = hypothesis
        self._decoder.speech_start_callback = speech_start

        # Set up built-in keyphrases if they set. Catch and log any
        # UnknownWordErrors because all keyphrases are optional.
        def get_phrase_values(name):
            phrase_attr = name + "_PHRASE"
            threshold_attr = name + "_PHRASE_THRESHOLD"
            return (getattr(self.config, phrase_attr, ""),
                    getattr(self.config, threshold_attr, 0))

        def safe_set_keyphrase(name, func):
            phrase, threshold = get_phrase_values(name)
            if phrase and threshold:
                try:
                    self.set_keyphrase(phrase, threshold, func)
                except UnknownWordError as e:
                    self._log.error(e)

        # Set the wake phrase using set_kws_list directly because it uses a
        # different search.
        wake_phrase, wake_threshold = get_phrase_values("WAKE")
        if wake_phrase and wake_threshold:
            try:
                self._validate_words(wake_phrase.split(), "keyphrase")
                self._decoder.set_kws_list("_wake_phrase", {
                    wake_phrase: wake_threshold
                })
            except UnknownWordError as e:
                self._log.error(e)

        # Set the other keyphrases using safe_set_keyphrase().
        safe_set_keyphrase("SLEEP", self.pause_recognition)
        safe_set_keyphrase("START_TRAINING",
                           self.start_training_session)
        safe_set_keyphrase("END_TRAINING",
                           self.end_training_session)

        # Set the PyAudioRecorder instance's config object.
        self._recorder.config = self.config

        # Start in sleep mode if requested.
        if self.config.START_ASLEEP:
            self.pause_recognition()
            self._log.warning("Starting in sleep mode as requested.")

    def _free_engine_resources(self):
        """
        Internal method for freeing the resources used by the engine.
        """
        # Stop the audio recorder if it is running.
        self._recognising = False
        self._recorder.stop()

        # Free the decoder and clear audio buffers.
        self._decoder = None
        self._audio_buffers = []

        # Reset other variables
        self._cancel_recognition_next_time = False
        self._training_session_active = False
        self._recognition_paused = False
        self._grammar_count = 0

        # Clear dictionaries and sets
        self._grammar_wrappers.clear()
        self._valid_searches.clear()
        self._keyphrase_thresholds.clear()
        self._keyphrase_functions.clear()

    def disconnect(self):
        """
        Deallocate the CMU Sphinx decoder and any other resources used by
        it.

        This method effectively unloads all loaded grammars and key
        phrases.
        """
        # Free resources if the decoder isn't currently being used to
        # recognise, otherwise stop the recognising loop, which will free
        # the resources safely.
        if not self.recognising:
            self._free_engine_resources()
        else:
            self._recognising = False
            self._recorder.stop()

    # -----------------------------------------------------------------------
    # Multiplexing timer methods.

    def create_timer(self, callback, interval, repeating=True):
        """
        Create and return a timer using the specified callback and repeat
        interval.

        **Note**: Timers will not run unless the engine is recognising
        audio. Normal threads can be used instead with no downsides.
        """
        if not self.recognising:
            self._log.warning("Timers will not run unless the engine is "
                              "recognising audio.")

        return super(SphinxEngine, self).create_timer(callback, interval,
                                                      repeating)

    # -----------------------------------------------------------------------
    # Methods for working with grammars.

    def check_valid_word(self, word):
        """
        Check if a word is in the current Sphinx pronunciation dictionary.

        :rtype: bool
        """
        if not self._decoder:
            self.connect()

        word = _map_to_str(word)
        return bool(self._decoder.lookup_word(word.lower()))

    def _validate_words(self, words, search_type):
        unknown_words = []

        # Use 'set' to de-duplicate the 'words' list.
        for word in set(words):
            if not self.check_valid_word(word):
                unknown_words.append(word)

        if unknown_words:
            # Sort the word list before using it.
            unknown_words.sort()
            raise UnknownWordError(
                "%s used words not found in the pronunciation dictionary: "
                "%s" % (search_type, ", ".join(unknown_words))
            )

    def _build_grammar_wrapper(self, grammar):
        search_name = "%d" % self._grammar_count
        self._grammar_count += 1
        return GrammarWrapper(grammar, self,
                              self._recognition_observer_manager,
                              search_name)

    def _set_grammar(self, wrapper, activate, partial=False):
        if not wrapper:
            return

        # Connect to the engine if it isn't connected already.
        self.connect()

        def activate_search_if_necessary():
            if activate:
                self._decoder.end_utterance()
                self._decoder.active_search = wrapper.search_name

        # Check if the wrapper's search name is valid.
        # Set the search (again) if necessary.
        valid_search = wrapper.search_name in self._valid_searches
        if valid_search and not wrapper.set_search:
            # wrapper.search_name is a valid search, so return.
            activate_search_if_necessary()
            return

        # Return early if 'partial' is True as an optimisation to avoid
        # recompiling grammars for every rule activation/deactivation.
        # Also return if the search doesn't need to be set.
        if partial or not wrapper.set_search:
            return

        # Compile and set the jsgf search.
        compiled = wrapper.compile_jsgf()
        self._log.debug(compiled)

        # Raise an error if there are no active public rules.
        if "public <root> = " not in compiled:
            raise EngineError("no public rules found in the grammar")

        # Set the JSGF search.
        self._decoder.end_utterance()
        self._decoder.set_jsgf_string(wrapper.search_name,
                                      _map_to_str(compiled))
        activate_search_if_necessary()

        # Grammar search has been loaded, so set the wrapper's flag.
        wrapper.set_search = False

    def _unset_search(self, name):
        # Unset a Pocket Sphinx search with the given name.
        # Don't unset the default or keyphrase searches.
        default_search = self._default_search_name
        reserved = [default_search] + self._keyphrase_search_names
        if name in reserved:
            return

        # Unset the Pocket Sphinx search.
        if name in self._valid_searches:
            # Unset the decoder search.
            self._decoder.unset_search(name)

            # Remove the search from the valid searches set.
            self._valid_searches.remove(name)

        # Change to the default search to avoid possible segmentation faults
        # from Pocket Sphinx which crash Python.
        self._set_default_search()

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
        :raises: UnknownWordError
        """
        # Check that all words in the keyphrase are in the pronunciation dictionary.
        # This can raise an UnknownWordError.
        self._validate_words(keyphrase.split(), "keyphrase")

        # Check that the threshold is a float.
        if not isinstance(threshold, float):
            raise TypeError("threshold must be a float, not %s" % threshold)

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

    def _set_default_search(self):
        # Change the active search to the one used for processing speech as
        # it is heard.
        swap_to_wake_search = (
            self.recognition_paused and self.config.WAKE_PHRASE and
            self.config.WAKE_PHRASE_THRESHOLD
        )

        # Ensure we're not processing.
        self._decoder.end_utterance()
        if swap_to_wake_search:
            self._decoder.active_search = "_wake_phrase"
        else:
            self._decoder.active_search = self._default_search_name

    def _load_grammar(self, grammar):
        """ Load the given *grammar* and return a wrapper. """
        self._log.debug("Engine %s: loading grammar %s."
                        % (self, grammar.name))
        wrapper = self._build_grammar_wrapper(grammar)

        # Attempt to set the grammar search.
        try:
            self._set_grammar(wrapper, False)
        except Exception as e:
            self._log.exception("Failed to load grammar %s: %s."
                                % (grammar, e))
            raise EngineError("Failed to load grammar %s: %s."
                              % (grammar, e))

        # Set the grammar wrapper's search name as valid and return the
        # wrapper.
        self._valid_searches.add(wrapper.search_name)
        return wrapper

    def _unload_grammar(self, grammar, wrapper):
        try:
            # Unset the search names for the grammar.
            self._unset_search(wrapper.search_name)
        except Exception as e:
            self._log.exception("Failed to unload grammar %s: %s."
                                % (grammar, e))

    def activate_grammar(self, grammar):
        self._log.debug("Activating grammar %s." % grammar.name)

    def deactivate_grammar(self, grammar):
        self._log.debug("Deactivating grammar %s." % grammar.name)

    def activate_rule(self, rule, grammar):
        self._log.debug("Activating rule %s in grammar %s."
                        % (rule.name, grammar.name))
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return
        try:
            wrapper.enable_rule(rule.name)
            self._set_grammar(wrapper, False, True)
        except Exception as e:
            self._log.exception("Failed to activate grammar %s: %s."
                                % (grammar, e))

    def deactivate_rule(self, rule, grammar):
        self._log.debug("Deactivating rule %s in grammar %s."
                        % (rule.name, grammar.name))
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return
        try:
            wrapper.disable_rule(rule.name)
            self._set_grammar(wrapper, False, True)
        except Exception as e:
            self._log.exception("Failed to activate grammar %s: %s."
                                % (grammar, e))

    def update_list(self, lst, grammar):
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return

        # Unfortunately there is no way to update lists for Pocket Sphinx
        # without reloading the grammar, so we'll update the list's JSGF
        # rule and reload.
        wrapper.update_list(lst)

        # Reload the grammar.
        try:
            self._set_grammar(wrapper, False)
        except Exception as e:
            self._log.exception("Failed to update list %s: %s."
                                % (lst, e))

    def set_exclusiveness(self, grammar, exclusive):
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return

        wrapper.exclusive = exclusive

    # -----------------------------------------------------------------------
    # Miscellaneous methods.

    @property
    def recognising(self):
        """
        Whether the engine is currently recognising speech.

        To stop recognition, use :meth:`disconnect`.

        :rtype: bool
        """
        return self._recorder.recording or self._recognising

    @property
    def default_search_result(self):
        """
        The last hypothesis object of the default search.

        This does not currently reach recognition observers because it is
        intended to be used for dictation results, which are currently
        disabled. Nevertheless this object can be useful sometimes.

        :returns: Sphinx Hypothesis object | None
        """
        return self._default_search_result

    @property
    def _default_search_name(self):
        # The name of the Pocket Sphinx search used for processing speech as
        # it is heard.
        return "_default"

    def _get_best_hypothesis(self, hypotheses):
        """
        Take a list of speech hypotheses and return the most likely one.

        :type hypotheses: iterable
        :return: str | None
        """
        # Get all distinct, non-null hypotheses.
        distinct = tuple([h for h in set(hypotheses) if bool(h)])
        if not distinct:
            return None
        elif len(distinct) == 1:
            return distinct[0]  # only one choice

        # Decide between non-null hypotheses using a Pocket Sphinx search with
        # each hypothesis as a grammar rule.
        grammar = RootGrammar()
        grammar.language_name = self.language
        for i, hypothesis in enumerate(distinct):
            grammar.add_rule(PublicRule("rule%d" % i, Literal(hypothesis)))

        compiled = grammar.compile_grammar()
        name = "_temp"

        # Store the current search name.
        original = self._decoder.active_search

        # Note that there is no need to validate words in this case because
        # each literal in the _temp grammar came from a Pocket Sphinx
        # hypothesis.
        self._decoder.end_utterance()
        self._decoder.set_jsgf_string(name, _map_to_str(compiled))
        self._decoder.active_search = name

        # Do the processing.
        hyp = self._decoder.batch_process(
            self._audio_buffers,
            use_callbacks=False
        )
        result = hyp.hypstr if hyp else None

        # Switch back to the previous search.
        self._decoder.end_utterance()  # just in case
        self._decoder.active_search = original
        self._decoder.unset_search("_temp")
        return result

    def _speech_start_callback(self, mimicking):
        # Get context info.
        fg_window = Window.get_foreground()
        window_info = {
            "executable": fg_window.executable,
            "title": fg_window.title,
            "handle": fg_window.handle,
        }

        # Call process_begin for all grammars so that any out of context
        # grammar will not be used.
        for wrapper in self._grammar_wrappers.copy().values():
            wrapper.process_begin(**window_info)

        if not mimicking:
            # Trim excess audio buffers from the start of the list. Keep a maximum 1
            # second of silence before speech start was detected. This should help
            # increase the performance of batch reprocessing later.
            chunk = self.config.FRAMES_PER_BUFFER
            rate = self.config.RATE
            seconds = 1
            n_buffers = int(rate / chunk * seconds)
            self._audio_buffers = self._audio_buffers[-1 * n_buffers:]

        # Notify observers
        self._recognition_observer_manager.notify_begin()

    def _hypothesis_callback(self, speech, mimicking):
        """
        Internal Pocket Sphinx hypothesis callback method. Calls _process_hypothesis
        and does post-processing afterwards.
        :param speech: speech hypothesis
        :type speech: str | None
        :param mimicking:  whether to treat speech as mimicked speech.
        :rtype: bool
        """
        # Clear any recorded audio buffers.
        self._recorder.clear_buffers()

        # Process speech. We should get back a boolean for whether processing
        # occurred as well as the final speech hypothesis.
        processing_occurred, final_speech = self._process_hypotheses(
            speech, mimicking
        )

        # Notify observers of failure.
        results_obj = None  # TODO Use PS results object once implemented
        if not processing_occurred:
            self._recognition_observer_manager.notify_failure(results_obj)

        # Write the training data files if necessary.
        data_dir = self.config.TRAINING_DATA_DIR
        if not mimicking and data_dir and os.path.isdir(data_dir):
            # Use the default search's hypothesis if final_speech was nil.
            if not final_speech:
                final_speech = speech
            try:
                write_training_data(self.config, self._audio_buffers,
                                    final_speech)
            except Exception as e:
                self._log.exception("Failed to write training data: %s" % e)

        # Clear audio buffer list because utterance processing has finished.
        self._audio_buffers = []

        # Ensure that the correct search is used.
        self._set_default_search()

        # Return whether processing occurred in case this method was called
        # by mimic.
        return processing_occurred

    def _process_key_phrases(self, speech, mimicking):
        """
        Processing key phrase searches and return the matched keyphrase
        (if any).

        :type speech: str
        :param mimicking: whether to treat speech as mimicked speech.
        :rtype: str
        """
        # Return if speech is empty/null or if there are no key phrases set.
        if not (speech and self._keyphrase_thresholds):
            return ""  # no matches

        if not mimicking:
            # Reprocess using the key phrases search
            self._decoder.end_utterance()
            self._decoder.active_search = "_key_phrases"
            hyp = self._decoder.batch_process(self._audio_buffers,
                                              use_callbacks=False)

            # Get the hypothesis string.
            speech = hyp.hypstr if hyp else ""

            # Restore search to the default search.
            self._set_default_search()

            # Return if no key phrase matched.
            if not speech:
                return ""

            # Handle multiple matching key phrases. This appears to be a
            # quirk of how Pocket Sphinx 'kws' searches work. Get the best
            # match instead if this is the case.
            recognised_phrases = speech.split("  ")
            if len(recognised_phrases) > 1:
                # Remove trailing space from the last phrase.
                recognised_phrases[len(recognised_phrases) - 1].rstrip()
                speech = self._get_best_hypothesis(recognised_phrases)
            else:
                speech = speech.rstrip()  # remove trailing whitespace.

        # Notify observers if a keyphrase was matched.
        results_obj = None  # TODO Use PS results object once implemented
        result = speech if speech in self._keyphrase_functions else ""
        words = tuple(result.split())
        if words:
            self._recognition_observer_manager.notify_recognition(
                words, None, None, results_obj
            )

        # Call the registered function if there was a match and the function
        # is callable.
        func = self._keyphrase_functions.get(speech, None)
        if callable(func):
            try:
                func()
            except Exception as e:
                self._log.exception(
                    "Exception caught when executing the function for "
                    "keyphrase '%s': %s" % (speech, e)
                )

        # Notify observers after calling the keyphrase function.
        if words:
            self._recognition_observer_manager.notify_post_recognition(
                words, None, None, results_obj
            )

        return result

    @classmethod
    def _generate_words_rules(cls, words, mimicking, all_dictation):
        # Convert words to Unicode, treat all uppercase words as dictation
        # words and other words as grammar words.
        # Minor note: this won't work for languages without capitalisation.
        result = []
        for word in words.split():
            if isinstance(word, binary_type):
                word = word.decode(locale.getpreferredencoding())
            if all_dictation or word.isupper() and mimicking:
                # Convert dictation words to lowercase for consistent
                # output.
                result.append((word.lower(), 1000000))
            else:
                result.append((word, 0))
        return tuple(result)

    def _process_hypotheses(self, speech, mimicking):
        """
        Internal method to process speech hypotheses. This should only be called
        from 'SphinxEngine._hypothesis_callback' because that method does important
        post processing.

        :param speech: speech
        :param mimicking: whether to treat speech as mimicked speech.
        :rtype: tuple
        """
        # Check key phrases search first.
        keyphrase = self._process_key_phrases(speech, mimicking)
        if keyphrase:
            # Keyphrase search matched.
            return True, keyphrase

        # Otherwise do grammar processing.
        processing_occurred = False
        hypotheses = {}
        wrappers = self._grammar_wrappers.copy().values()

        # Save the LM hypothesis separately because it will almost always be favoured
        # over grammar hypotheses.
        lm_hypothesis = speech

        # Count exclusive grammars.
        exclusive_count = 0
        for wrapper in wrappers:
            if wrapper.exclusive:
                exclusive_count += 1

        # Collect each active grammar wrapper.
        # Only include exclusive grammars if at least one is loaded.
        if exclusive_count:
            wrappers = [w for w in wrappers
                        if w.exclusive and w.grammar_active]
        else:
            wrappers = [w for w in wrappers if w.grammar_active]

        # No grammar has been loaded.
        if not wrappers:
            return processing_occurred, speech

        # Batch process audio buffers for each active grammar. Store each
        # hypothesis.
        for wrapper in wrappers:
            if mimicking:
                # Just use 'speech' for everything if mimicking.
                hyp = speech
            else:
                # Switch to the search for this grammar and re-process the
                # audio.
                self._set_grammar(wrapper, True)
                hyp = self._decoder.batch_process(
                    self._audio_buffers,
                    use_callbacks=False
                )
                if hyp:
                    hyp = hyp.hypstr

            # Set the hypothesis in the dictionary.
            hypotheses[wrapper.search_name] = hyp

        # Get the best hypothesis.
        speech = self._get_best_hypothesis(list(hypotheses.values()))
        if not speech and not lm_hypothesis:
            return processing_occurred, speech

        if speech:
            # Process speech using the first matching grammar.
            words_rules = self._generate_words_rules(speech, mimicking, False)
            for wrapper in wrappers:
                if hypotheses[wrapper.search_name] != speech:
                    continue

                processing_occurred = wrapper.process_words(words_rules)
                if processing_occurred:
                    break

        if not processing_occurred:
            # Process grammars using the LM hypothesis as dictation words.
            dictation_words = self._generate_words_rules(lm_hypothesis, mimicking,
                                                         True)
            for wrapper in wrappers:
                processing_occurred = wrapper.process_words(dictation_words)
                if processing_occurred:
                    break

        # Return whether processing occurred and the final speech hypothesis for
        # post processing.
        return processing_occurred, speech

    def process_buffer(self, buf):
        """
        Recognise speech from an audio buffer.

        This method is meant to be called in sequence for multiple audio
        buffers. It will do nothing if :meth:`connect` hasn't been called.

        :param buf: audio buffer
        :type buf: str
        """
        if not self._decoder:
            return

        # Cancel current recognition if it has been requested.
        if self._cancel_recognition_next_time:
            self._decoder.end_utterance()
            self._audio_buffers = []
            self._cancel_recognition_next_time = False

        # Keep a list of buffers for possible reprocessing using different Pocket
        # Sphinx searches later.
        self._audio_buffers.append(buf)

        # Call the timer callback if it is set.
        self.call_timer_callback()

        # Process audio.
        try:
            self._recognising = True
            self._decoder.process_audio(buf)
        finally:
            self._recognising = False

    def process_wave_file(self, path):
        """
        Recognise speech from a wave file and return the recognition results.

        This method checks that the wave file is valid. It raises an error
        if the file doesn't exist, if it can't be read or if the WAV header
        values do not match those in the engine configuration.

        If recognition is paused (sleep mode), this method will call
        :meth:`resume_recognition`.

        The wave file must use the same sample width, sample rate and number
        of channels that the acoustic model uses.

        If the file is valid, :meth:`process_buffer` is then used to process
        the audio.

        Multiple utterances are supported.

        :param path: wave file path
        :raises: IOError | OSError | ValueError
        :returns: recognition results
        :rtype: generator
        """
        if not self._decoder:
            self.connect()

        # This method's implementation has been adapted from the PyAudio
        # play wave example:
        # http://people.csail.mit.edu/hubert/pyaudio/#play-wave-example

        # Check that path is a valid file.
        if not os.path.isfile(path):
            raise IOError("'%s' is not a file. Please use a different file path.")

        # Get required audio configuration from the engine config.
        channels, sample_width, rate, chunk = (
            self.config.CHANNELS,
            self.config.SAMPLE_WIDTH,
            self.config.RATE,
            self.config.FRAMES_PER_BUFFER
        )

        # Make sure recognition is not paused.
        if self.recognition_paused:
            self.resume_recognition(notify=False)

        # Open the wave file. Use contextlib to make sure that the file is
        # closed whether errors are raised or not.
        # Also register a custom recognition observer for the duration.
        obs = WaveRecognitionObserver(self)
        with contextlib.closing(wave.open(path, "rb")) as wf, obs as obs:
            # Validate the wave file's header.
            if wf.getnchannels() != channels:
                message = ("WAV file '%s' should use %d channel(s), not %d!"
                           % (path, channels, wf.getnchannels()))
            elif wf.getsampwidth() != sample_width:
                message = ("WAV file '%s' should use sample width %d, not "
                           "%d!" % (path, sample_width, wf.getsampwidth()))
            elif wf.getframerate() != rate:
                message = ("WAV file '%s' should use sample rate %d, not "
                           "%d!" % (path, rate, wf.getframerate()))
            else:
                message = None

            if message:
                raise ValueError(message)

            # Use process_buffer to process each buffer.
            for _ in range(0, int(wf.getnframes() / chunk) + 1):
                data = wf.readframes(chunk)
                if not data:
                    break

                self.process_buffer(data)

                # Get the results from the observer.
                if obs.words:
                    yield obs.words
                    obs.words = ""

        # Log warnings if speech start or end weren't detected.
        if not obs.complete:
            self._log.warning("Speech start/end wasn't detected in the wave "
                              "file!")
            self._log.warning("Perhaps the Sphinx '-vad_prespeech' value "
                              "should be higher?")
            self._log.warning("Or maybe '-vad_startspeech' or "
                              "'-vad_postspeech' should be lower?")

    def _do_recognition(self):
        """
        Start recognising from the default recording device until
        :meth:`disconnect` is called.

        Recognition can be paused and resumed using either the sleep/wake
        key phrases or by calling :meth:`pause_recognition` or
        :meth:`resume_recognition`.

        To configure audio input settings, modify the engine's ``CHANNELS``,
        ``RATE``, ``SAMPLE_WIDTH`` and/or ``FRAMES_PER_BUFFER``
        configuration options.
        """
        if not self._decoder:
            self.connect()

        # Start recognising in a loop.
        self._recorder.start()
        self._cancel_recognition_next_time = False
        while self.recognising:
            for buf in self._recorder.get_buffers():
                self.process_buffer(buf)

        # Free engine resources after recognition has stopped.
        self._free_engine_resources()

    def mimic(self, words):
        """ Mimic a recognition of the given *words* """
        if isinstance(words, (list, tuple)):
            words = " ".join(words)

        # Fail on empty input.
        if not words:
            raise MimicFailure("Invalid mimic input %r" % words)

        if self.recognition_paused and words == self.config.WAKE_PHRASE:
            self.resume_recognition()
            return

        # Pretend that Sphinx has started processing speech
        self._speech_start_callback(True)

        # Process the words as if they were spoken
        result = self._hypothesis_callback(words, True)
        if not result:
            raise MimicFailure("No matching rule found for words %s."
                               % words)

    def mimic_phrases(self, *phrases):
        """
        Mimic a recognition of the given *phrases*.

        This method accepts variable phrases instead of a list of words.
        """
        # Pretend that Sphinx has started processing speech
        self._speech_start_callback(True)

        # Process phrases as if they were spoken
        wake_phrase = self.config.WAKE_PHRASE
        for phrase in phrases:
            if self.recognition_paused and phrase == wake_phrase:
                self.resume_recognition()
                continue

            result = self._hypothesis_callback(phrase, True)
            if not result:
                raise MimicFailure("No matching rule found for words %s."
                                   % phrase)

    def speak(self, text):
        """"""
        self._log.warning("text-to-speech is not implemented for this "
                          "engine.")
        self._log.warning("Printing text instead.")
        print(text)

    def _get_language(self):
        return self.config.LANGUAGE

    def _has_quoted_words_support(self):
        return False

    # ----------------------------------------------------------------------
    # Training-related methods

    def write_transcript_files(self, fileids_path, transcription_path):
        """
        Write .fileids and .transcription files for files in the training
        data directory and write them to the specified file paths.

        This method will raise an error if the ``TRAINING_DATA_DIR``
        configuration option is not set to an existing directory.

        :param fileids_path: path to .fileids file to create.
        :param transcription_path: path to .transcription file to create.
        :type fileids_path: str
        :type transcription_path: str
        :raises: IOError | OSError
        """
        write_transcript_files(
            self.config, fileids_path, transcription_path
        )

    @property
    def training_session_active(self):
        """
        Whether a training session is in progress.

        :rtype: bool
        """
        return self._training_session_active

    def start_training_session(self):
        """
        Start the training session. This will stop recognition processing
        until either :meth:`end_training_session` is called or the end
        training keyphrase is heard.
        """
        data_dir = self.config.TRAINING_DATA_DIR
        if not data_dir or not os.path.isdir(data_dir):
            self._log.warning("Training data will not be recorded; '%s' is "
                              "not a directory" % data_dir)

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
        """
        if self._training_session_active:
            self._log.info("Ending training session.")
            self._log.info("Rule actions will now be processed normally "
                           "again.")
            self._training_session_active = False

    # ----------------------------------------------------------------------
    # Recognition loop control methods
    # Stopping recognition loop is done using disconnect()

    @property
    def recognition_paused(self):
        """
        Whether the engine is waiting for the wake phrase to be heard or for
        :meth:`resume_recognition` to be called.

        :rtype: bool
        """
        return self._recognition_paused

    def pause_recognition(self):
        """
        Pause recognition and wait for :meth:`resume_recognition` to be
        called or for the wake keyphrase to be spoken.
        """
        if not self._decoder:
            return

        self._recognition_paused = True

        # Switch to the wake keyphrase search if a wake keyphrase has been
        # set.
        self._set_default_search()
        if not self.config.WAKE_PHRASE:
            self._log.warning("No wake phrase has been set.")
            self._log.warning("Use engine.resume_recognition() to wake up.")

        # Define temporary callback for the decoder.
        def hypothesis(hyp):
            # Clear any recorded audio buffers.
            self._recorder.clear_buffers()
            s = hyp.hypstr if hyp else None

            # Resume recognition if s is the wake keyphrase.
            if s and s.strip() == self.config.WAKE_PHRASE.strip():
                self.resume_recognition()
            elif self.config.WAKE_PHRASE:
                self._log.debug("Didn't hear %s" % self.config.WAKE_PHRASE)

            # Clear audio buffers
            self._audio_buffers = []

        # Override decoder hypothesis callback.
        self._decoder.hypothesis_callback = hypothesis

    def resume_recognition(self, notify=True):
        """
        Resume listening for grammar rules and key phrases.
        """
        if not self._decoder:
            return

        self._recognition_paused = False

        # Notify observers about recognition resume.
        keyphrase = self.config.WAKE_PHRASE
        words = tuple(keyphrase.strip().split())
        results_obj = None  # TODO Use PS results object once implemented
        if words and notify:
            manager = self._recognition_observer_manager
            arguments = (words, None, None, results_obj)
            manager.notify_recognition(*arguments)
            manager.notify_post_recognition(*arguments)

        # Restore the callbacks to normal
        def hypothesis(hyp):
            # Set default search result.
            self._default_search_result = hyp

            # Set speech to the hypothesis string or None if there isn't one
            speech = hyp.hypstr if hyp else None
            return self._hypothesis_callback(speech, False)

        self._decoder.hypothesis_callback = hypothesis

        # Switch to the default search.
        self._set_default_search()

    def cancel_recognition(self):
        """
        If a recognition was in progress, cancel it before processing the
        next audio buffer.
        """
        self._cancel_recognition_next_time = True
