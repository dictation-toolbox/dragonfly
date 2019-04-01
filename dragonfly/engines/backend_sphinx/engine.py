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

from six import text_type, PY2

from dragonfly import Window
from .dictation import SphinxDictationContainer
from .recobs import SphinxRecObsManager
from .training import TrainingDataWriter
from ..base import EngineBase, EngineError, MimicFailure

try:
    from jsgf import RootGrammar, PublicRule, Literal
    from pyaudio import PyAudio
    from sphinxwrapper import PocketSphinx, search_arguments_set

    from .compiler import SphinxJSGFCompiler
    from .grammar_wrapper import GrammarWrapper
except ImportError:
    # Import a few things here optionally for readability (the engine won't start
    # without them) and so that autodoc can import this module without them.
    pass


class UnknownWordError(Exception):
    pass


class SphinxEngine(EngineBase):
    """ Speech recognition engine back-end for CMU Pocket Sphinx. """

    _name = "sphinx"
    DictationContainer = SphinxDictationContainer

    def __init__(self):
        EngineBase.__init__(self)

        # Set up the engine logger
        logging.basicConfig()

        try:
            import sphinxwrapper
            import jsgf
            import pyaudio
        except ImportError:
            self._log.error("%s: Failed to import jsgf, pyaudio and/or "
                            "sphinxwrapper. Are they installed?" % self)
            raise EngineError("Failed to import Pocket Sphinx engine dependencies.")

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
        self._keyphrase_thresholds = {}
        self._keyphrase_functions = {}

        # Set up keyphrase search names and valid search names for grammars.
        self._keyphrase_search_names = ["_key_phrases", "_wake_phrase"]
        self._valid_searches = set()

        # Recognising loop control variables
        self._recognising = False
        self._cancel_recognition_next_time = False
        self._recognition_paused = False

        # Training data writer, initialised on connect().
        self._training_data_writer = None

        # Variable used in training sessions.
        self._training_session_active = False

    @property
    def config(self):
        """
        Python module/object containing engine configuration.

        Setting this property will raise an :class:`EngineError` if the
        given configuration object doesn't define each required
        configuration option.

        You will need to restart the engine with :meth:`disconnect` and
        :meth:`connect` if the configuration has been changed after
        :meth:`connect` has been called.

        :raises: EngineError
        :returns: config module/object
        """
        return self._config

    @config.setter
    def config(self, value):
        # Validate configuration module
        self.validate_config(value)
        self._config = value

    @classmethod
    def validate_config(cls, engine_config):
        required_attributes = [
            "DECODER_CONFIG", "PYAUDIO_STREAM_KEYWORD_ARGS", "LANGUAGE",
            "NEXT_PART_TIMEOUT", "START_ASLEEP"
        ]
        not_preset = []
        for attr in required_attributes:
            if not hasattr(engine_config, attr):
                not_preset.append(attr)

        if not_preset:
            # Raise an error with the required attributes that weren't set.
            not_preset.sort()
            raise EngineError("invalid engine configuration. The following "
                              "required attributes were not present: %s"
                              % ", ".join(not_preset))

        # Check optional config attributes. Set default values for any
        # missing attributes.
        training_dir = "TRAINING_DATA_DIR"
        if not hasattr(engine_config, training_dir):
            setattr(engine_config, training_dir, "")

        # Check which built-in key phrases are present and have values.
        # All of these can be overridden with "" (or equiv.) to be disabled.
        defaults = {
            "WAKE": ("wake up", 1e-20),
            "SLEEP": ("go to sleep", 1e-40),
            "START_TRAINING": ("start training session", 1e-48),
            "END_TRAINING": ("end training session", 1e-45),
        }

        def set_builtin_phrase_attributes(name):
            # Set default values if 'engine_config' does not define the
            # attributes.
            phrase_attr = name + "_PHRASE"
            threshold_attr = name + "_PHRASE_THRESHOLD"
            d_phrase, d_threshold = defaults[name]
            if not hasattr(engine_config, phrase_attr):
                setattr(engine_config, phrase_attr, d_phrase)
            if not hasattr(engine_config, threshold_attr):
                setattr(engine_config, threshold_attr, d_threshold)

        for phrase in defaults.keys():
            set_builtin_phrase_attributes(phrase)

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
        self._valid_searches.add(self._dictation_search_name)

        # Set up callback function wrappers
        def hypothesis(hyp):
            # Set speech to the hypothesis string or None if there isn't one
            speech = hyp.hypstr if hyp else None
            return self._hypothesis_callback(speech, False)

        def speech_start():
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

        # Initialise a TrainingDataWriter instance if necessary.
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
        # Free the decoder and clear the audio buffer list
        self._decoder = None
        self._audio_buffers = []

        # Reset other variables
        self._cancel_recognition_next_time = False
        self._training_session_active = False
        self._recognition_paused = False

        # Close the training data files and discard the writer if necessary.
        if self._training_data_writer:
            self._training_data_writer.close_files()
            self._training_data_writer = None

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
            raise UnknownWordError(
                "%s used words not found in the pronunciation dictionary: "
                "%s" % (search_type, ", ".join(unknown_words)))

    def _build_grammar_wrapper(self, grammar):
        return GrammarWrapper(grammar, self)

    def _set_grammar(self, wrapper, activate, partial=False):
        if not wrapper:
            return

        # Connect to the engine if it isn't connected already.
        self.connect()

        # Don't allow grammar wrappers to use keyphrase search names.
        if wrapper.search_name in self._keyphrase_search_names:
            raise EngineError("grammar cannot be loaded because '%s' is a "
                              "reserved name" % wrapper.search_name)

        def activate_search_if_necessary():
            if activate:
                self._decoder.end_utterance()
                self._decoder.active_search = wrapper.search_name

        # Check if the wrapper's search_name is valid
        if wrapper.search_name in self._valid_searches:
            # wrapper.search_name is a valid search, so return.
            activate_search_if_necessary()
            return

        # Return early if 'partial' is True as an optimisation to avoid
        # recompiling grammars for every rule activation/deactivation.
        if partial:
            return

        # Compile and set the jsgf search.
        compiled = wrapper.compile_jsgf()

        # Only set the grammar's search if there are still active rules.
        if "public <root> = " not in compiled:
            return

        # Check that each word in the grammar is in the pronunciation
        # dictionary. This will raise an UnknownWordError if one or more
        # aren't.
        self._validate_words(wrapper.grammar_words,
                             "grammar '%s'" % wrapper.grammar.name)

        # Set the JSGF search.
        self._decoder.end_utterance()
        self._decoder.set_jsgf_string(wrapper.search_name, compiled)
        activate_search_if_necessary()

        # Grammar search has been loaded, add the search name to the set.
        self._valid_searches.add(wrapper.search_name)

    def _unset_search(self, name):
        # Unset a Pocket Sphinx search with the given name.
        # Note that this method will not unset the dictation or keyphrase
        # searches.
        dictation_search = self._dictation_search_name
        reserved = [dictation_search] + self._keyphrase_search_names
        if name in reserved:
            return

        # Unset the Pocket Sphinx search.
        if name in self._valid_searches:
            # Unfortunately, the C function for doing this (ps_unset_search)
            # is not exposed. Pocket Sphinx searches are pretty lighweight
            # however. This would only be an issue on hardware with limited
            # memory.

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

    def _set_dictation_search(self):
        # Change the active search to the one used for recognising dictation.
        self._decoder.end_utterance()  # ensure we're not processing
        self._decoder.active_search = self._dictation_search_name

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
            self._set_grammar(wrapper, False)
        except UnknownWordError as e:
            # Unknown words should be logged as plain error messages, not
            # exception stack traces.
            self._log.error(e)
            raise EngineError("Failed to load grammar %s: %s."
                              % (grammar, e))
        except Exception as e:
            self._log.exception("Failed to load grammar %s: %s."
                                % (grammar, e))
            raise EngineError("Failed to load grammar %s: %s."
                              % (grammar, e))
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
            self._unset_search(wrapper.search_name)
            self._set_grammar(wrapper, False, True)
        except UnknownWordError as e:
            self._log.error(e)
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
            self._unset_search(wrapper.search_name)
            self._set_grammar(wrapper, False, True)
        except UnknownWordError as e:
            self._log.error(e)
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
        self._unset_search(wrapper.search_name)
        try:
            self._set_grammar(wrapper, False)
        except Exception as e:
            self._log.exception("Failed to update list %s: %s."
                                % (lst, e))

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

    @property
    def recognising(self):
        """
        Whether the engine is recognising speech in a loop.

        To stop recognition, use :meth:`disconnect`.

        :rtype: bool
        """
        return self._recognising

    @property
    def _dictation_search_name(self):
        # The name of the Pocket Sphinx search used for processing speech as
        # dictation.
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
        self._decoder.set_jsgf_string(name, compiled)
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
        return result

    def _speech_start_callback(self, mimicking):
        # Get context info. Dragonfly has a handy static method for this:
        fg_window = Window.get_foreground()

        # Call process_begin for all grammars so that any out of context
        # grammar will not be used.
        for wrapper in self._grammar_wrappers.values():
            wrapper.process_begin(fg_window)

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
        # Process speech. We should get back a boolean for whether processing
        # occurred as well as the final speech hypothesis.
        processing_occurred, speech = self._process_hypotheses(
            speech, mimicking
        )
        self._set_dictation_search()

        # Notify observers of failure.
        if not processing_occurred:
            self._recognition_observer_manager.notify_failure()

        # Finalise the current training data and open a new wav file.
        # If speech is None, the current .wav file will be discarded.
        if self._training_data_writer and not mimicking:
            self._training_data_writer.finalise(speech)
            self._training_data_writer.open_next_wav_file()

        # Clear the internal audio buffer list because it is no longer
        # needed.
        self._audio_buffers = []

        # Return whether processing occurred in case this method was called
        # by mimic.
        return processing_occurred

    def _process_key_phrases(self, speech, mimicking):
        """
        Processing key phrase searches and return the matched keyphrase (if any).

        :type speech: str
        :param mimicking: whether to treat speech as mimicked speech.
        :rtype: str
        """
        if not speech:
            return ""  # no matches

        if not mimicking:
            # Reprocess using the key phrases search
            self._decoder.end_utterance()
            self._decoder.active_search = "_key_phrases"
            hyp = self._decoder.batch_process(self._audio_buffers,
                                              use_callbacks=False)

            # Get the hypothesis string.
            speech = hyp.hypstr if hyp else ""

            # Restore search to the dictation search.
            self._set_dictation_search()

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

        # Return speech if it matched a keyphrase.
        result = speech if speech in self._keyphrase_functions else ""
        return result

    @classmethod
    def _generate_words_rules(cls, words, mimicking):
        # Convert words to Unicode, treat all uppercase words as dictation
        # words and other words as grammar words.
        # Minor note: this won't work for languages without capitalisation.
        result = []
        for word in words.split():
            if PY2 and isinstance(word, str):
                word = text_type(word, encoding="utf-8")
            if word.isupper() and mimicking:
                # Convert dictation words to lowercase for consistent output.
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
            # Keyphrase search matched. Notify observers and return True.
            words = tuple(keyphrase.split())
            self._recognition_observer_manager.notify_recognition(words)
            return True, keyphrase

        # Otherwise do grammar processing.
        processing_occurred = False
        hypotheses = {self._dictation_search_name: speech}

        # Collect each active grammar's GrammarWrapper.
        wrappers = [w for w in self._grammar_wrappers.values()
                    if w.grammar_active]

        # No grammar has been loaded.
        if not wrappers:
            # TODO What should we do here? Output formatted Dictation like DNS?
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

        # TODO Decide whether including the LM hypothesis is worth it
        # hypotheses.pop(self._dictation_search_name)

        # Get the best hypothesis.
        speech = self._get_best_hypothesis(list(hypotheses.values()))
        if not speech:
            return processing_occurred, speech

        # Process speech using the matching grammar(s).
        words_rules = self._generate_words_rules(speech, mimicking)
        for wrapper in wrappers:
            if hypotheses[wrapper.search_name] != speech:
                continue

            processing_occurred = wrapper.process_words(words_rules)
            if processing_occurred:
                # Notify observers of the recognition.
                self._recognition_observer_manager.notify_recognition(
                    tuple([word for word, _ in words_rules])
                )
                break

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
            self._log.info("Starting in sleep mode as requested.")

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

        if self.recognition_paused and words == self.config.WAKE_PHRASE:
            self.resume_recognition()
            return

        # Pretend that Sphinx has started processing speech
        self._speech_start_callback(True)

        # Process the words as if they were spoken
        result = self._hypothesis_callback(words, True)
        if not result:
            raise MimicFailure("No matching rule found for words %s." % words)

    def mimic_phrases(self, *phrases):
        """
        Mimic a recognition of the given *phrases*.

        This method accepts variable phrases instead of a list of words to allow
        mimicking of rules using :class:`Dictation` elements.
        """
        wake_phrase = self.config.WAKE_PHRASE
        if self.recognition_paused and " ".join(phrases) == wake_phrase:
            self.resume_recognition()
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
        """"""
        self._log.warning("text-to-speech is not implemented for this "
                          "engine.")
        self._log.warning("Printing text instead.")
        print(text)

    def _get_language(self):
        return self.config.LANGUAGE

    # ---------------------------------------------------------------------
    # Training session methods

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
        until either :meth:`end_training_session` is called or the end training
        keyphrase is heard.
        """
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
        """
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
        return self._recognition_paused

    def pause_recognition(self):
        """
        Pause recognition and wait for :meth:`resume_recognition` to be called or
        for the wake keyphrase to be spoken.
        """
        if not self._decoder:
            return

        self._recognition_paused = True

        # Switch to the wake keyphrase search if a wake keyphrase has been
        # set.
        if self.config.WAKE_PHRASE:
            self._decoder.end_utterance()
            self._decoder.active_search = "_wake_phrase"
        else:
            self._log.warning("No wake phrase has been set.")
            self._log.warning("Use engine.resume_recognition() to wake up.")

        # Define temporary callback for the decoder.
        def hypothesis(hyp):
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

    def resume_recognition(self):
        """
        Resume listening for grammar rules and key phrases.
        """
        if not self._decoder:
            return

        self._recognition_paused = False

        # Notify observers about recognition resume.
        keyphrase = self.config.WAKE_PHRASE
        words = tuple(keyphrase.strip().split())
        self._recognition_observer_manager.notify_recognition(words)

        # Restore the callbacks to normal
        def hypothesis(hyp):
            # Set speech to the hypothesis string or None if there isn't one
            speech = hyp.hypstr if hyp else None
            return self._hypothesis_callback(speech, False)

        self._decoder.hypothesis_callback = hypothesis

        # Switch to the dictation search.
        self._set_dictation_search()

    def cancel_recognition(self):
        """
        If a recognition was in progress, cancel it before processing the next
        audio buffer.
        """
        self._cancel_recognition_next_time = True
