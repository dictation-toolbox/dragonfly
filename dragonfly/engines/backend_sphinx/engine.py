#
# This file is part of Dragonfly.
# (c) Copyright 2017-2023 by Dane Finlay
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

import locale
import os

from six            import binary_type, text_type, string_types, PY2
from jsgf           import RootGrammar, PublicRule, Literal
from sphinxwrapper  import PocketSphinx
from pocketsphinx   import Hypothesis

import dragonfly.engines
from dragonfly.windows.window                         import Window
from dragonfly.engines.base                           import (EngineBase, EngineError, MimicFailure,
                                                              DelegateTimerManagerInterface)
from dragonfly.engines.backend_sphinx.compiler         import SphinxJSGFCompiler
from dragonfly.engines.backend_sphinx.grammar_wrapper  import GrammarWrapper
from dragonfly.engines.backend_sphinx.misc           import (EngineConfig,
                                                             get_decoder_config_object)
from dragonfly.engines.backend_sphinx.recobs           import SphinxRecObsManager
from dragonfly.engines.backend_sphinx.recording        import AudioRecorder
from dragonfly.engines.backend_sphinx.timer            import SphinxTimerManager


#---------------------------------------------------------------------------

class UnknownWordError(Exception):
    pass


def _map_to_str(text, encoding=locale.getpreferredencoding()):
    # Decoder methods require *str* objects, so translate unicode/bytes to
    #  whatever *str* is in this version of Python.
    if not isinstance(text, string_types):
        text = str(text)
    if PY2 and isinstance(text, text_type):
        text = text.encode(encoding)
    elif not PY2 and isinstance(text, binary_type):
        text = text.decode(encoding)
    return text


#---------------------------------------------------------------------------

class SphinxEngine(EngineBase, DelegateTimerManagerInterface):
    """ Speech recognition engine back-end for CMU Pocket Sphinx. """

    _name = "sphinx"

    def __init__(self):
        EngineBase.__init__(self)
        DelegateTimerManagerInterface.__init__(self)

        try:
            import sphinxwrapper, jsgf, sounddevice
        except ImportError:
            raise EngineError("Failed to import Pocket Sphinx engine "
                              "dependencies.")

        # Set the default engine configuration.
        # This can be changed later using the config property.
        self._config = None
        self.config = EngineConfig

        # Initialize members.
        self._decoder = None
        self._audio_buffers = []
        self._grammar_count = 0
        self._null_hypothesis = Hypothesis("", 0, 0)
        self._default_search_name = "_default"
        self._valid_searches = {"_default"}
        self.compiler = SphinxJSGFCompiler(self)
        self._recognition_observer_manager = SphinxRecObsManager(self)
        self._timer_manager = SphinxTimerManager(0.02, self)
        self._recorder = AudioRecorder(self.config)
        self._doing_recognition = False
        self._deferred_disconnect = False
        self._mimicking = False

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

            "CHANNELS",
            "RATE",
            "SAMPLE_WIDTH",
            "FORMAT",
            "BUFFER_SIZE",
        ]

        # Get default values and set them they are missing.
        for option in options:
            if hasattr(engine_config, option):
                continue

            default_value = getattr(EngineConfig, option)
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

        # Set up callback function wrappers.
        def hypothesis(hyp):
            # Ensure that an Hypothesis object is used.
            if hyp is None: hyp = self._null_hypothesis

            # Call the engine's hypothesis method.
            return self._hypothesis_callback(hyp)

        def speech_start():
            return self._speech_start_callback()

        self._decoder.hypothesis_callback = hypothesis
        self._decoder.speech_start_callback = speech_start

        # Set the AudioRecorder instance's config object.
        self._recorder.config = self.config

    def disconnect(self):
        """
        Deallocate the CMU Sphinx decoder and any other resources used by
        it.  If the engine is currently recognizing, the recognition loop
        will be terminated first.

        This method unloads all loaded grammars.
        """
        # If the engine is currently recognizing, instruct it to free engine
        #  resources in the next iteration of the recognition loop.
        #  Otherwise, free engine resources now.
        if self._doing_recognition: self._deferred_disconnect = True
        else:                       self._free_engine_resources()

    def _free_engine_resources(self):
        """
        Internal method for freeing the resources used by the engine.
        """
        # Stop the audio recorder if it is running.
        self._recorder.stop()

        # Clear audio buffers.
        while len(self._audio_buffers) > 0:
            self._audio_buffers.pop(0)

        # Unload all grammars.
        # Note: copy() is used here because unloading removes items from the
        #  grammar wrapper dictionary.
        for wrapper in self._grammar_wrappers.copy().values():
            wrapper.grammar.unload()

        # Reset variables.
        self._grammar_count = 0
        self._doing_recognition = False
        self._deferred_disconnect = False
        self._mimicking = False

        # Deallocate the decoder.
        self._decoder = None

    #-----------------------------------------------------------------------
    # Multiplexing timer methods.

    def create_timer(self, callback, interval, repeating=True):
        """
        Create and return a timer using the specified callback and repeat
        interval.

        .. note::

           Timers only run when the engine is processing audio.

        """
        return super(SphinxEngine, self).create_timer(callback, interval,
                                                      repeating)

    #-----------------------------------------------------------------------
    # Methods for working with grammars.

    def _load_grammar(self, grammar):
        """ Load the given *grammar* and return a wrapper. """
        self._log.debug("Engine %s: loading grammar %s."
                        % (self, grammar.name))
        search_name = "%d" % self._grammar_count
        self._grammar_count += 1
        wrapper = GrammarWrapper(grammar, self, search_name)

        # Attempt to set the grammar search.
        try:
            self._set_grammar(wrapper, False)
        except Exception as e:
            self._log.exception("Failed to load grammar %s: %s."
                                % (grammar, e))
            raise EngineError("Failed to load grammar %s: %s."
                              % (grammar, e))

        # Set the grammar's search name as valid and return.
        self._valid_searches.add(search_name)
        return wrapper

    def _unload_grammar(self, grammar, wrapper):
        try:
            # Unset the search names for the grammar.
            self._unset_search(wrapper.search_name)
        except Exception as e:
            self._log.exception("Failed to unload grammar %s: %s."
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

    def set_exclusiveness(self, grammar, exclusive):
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return

        wrapper.exclusive = exclusive

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

        # Nothing further to do; no public rules.
        if "public <root> = " not in compiled:
            wrapper.set_search = False
            return

        # Set the JSGF search.
        self._decoder.end_utterance()
        self._decoder.set_jsgf_string(wrapper.search_name,
                                      _map_to_str(compiled))
        activate_search_if_necessary()

        # Grammar search has been loaded, so set the wrapper's flag.
        wrapper.set_search = False

    def _unset_search(self, name):
        # Unset a Pocket Sphinx search with the given name.
        # Do NOT unset the default search; this will cause a segfault!
        if name == self._default_search_name:
            return

        # Unset the Pocket Sphinx decoder search.
        if name in self._valid_searches:
            self._decoder.unset_search(name)
            self._valid_searches.remove(name)

        # Switch back to the always-available default search.
        self._set_default_search()

    def _set_default_search(self):
        # Ensure we're not processing.
        self._decoder.end_utterance()

        # Set the default search.
        self._decoder.active_search = self._default_search_name

    def check_valid_word(self, word):
        """
        Check if a word is in the current Sphinx pronunciation dictionary.

        :rtype: bool
        """
        if not self._decoder:
            self.connect()

        word = _map_to_str(word)
        return bool(self._decoder.lookup_word(word.lower()))

    #------------------------------------------------------------------------
    # Recognition methods.

    def _do_recognition(self):
        """
        Start recognizing from the default recording device until stopped by
        a keyboard interrupt or a call to :meth:`disconnect`.

        To configure audio input settings, modify the engine's ``CHANNELS``,
        ``RATE``, ``SAMPLE_WIDTH`` ``FORMAT`` and/or ``BUFFER_SIZE``
        configuration options.
        """
        if not self._decoder:
            self.connect()

        # Start recognizing from the microphone in a loop.
        # If disconnect is called while this loop is running, free engine
        #  resources and stop.
        recorder = self._recorder
        recorder.start()
        try:
            self._doing_recognition = True
            while self._doing_recognition:
                for buf in recorder.get_buffers():
                    self.process_buffer(buf)
                    if self._deferred_disconnect:
                        self._free_engine_resources()
                        break
        finally:
            self._doing_recognition = False
            self._recorder.stop()

    def mimic(self, words):
        """ Mimic a recognition of the given *words* """
        # The *words* argument should be a string or iterable.
        # Words are put into lowercase for consistency.
        if isinstance(words, string_types):
            text = words.lower()
        elif iter(words):
            text = " ".join([w.lower() for w in words])
        else:
            raise TypeError("%r is not a string or other iterable object"
                            % words)

        # Fail on empty input.
        if not words:
            raise MimicFailure("Invalid mimic input %r" % words)

        # Process the words as if they were spoken.
        self._mimicking = True
        try:
            self._speech_start_callback()
            hyp = MimickedHypothesis(text, 0, 0)
            result = self._hypothesis_callback(hyp)
        finally:
            self._mimicking = False

        if not result:
            raise MimicFailure("No matching rule found for words %s."
                               % words)

    def process_buffer(self, buf):
        """
        Recognize speech from an audio buffer.

        This method is meant to be called sequentially with buffers from an
        audio source, such as a microphone or wave file.

        This method will do nothing if :meth:`connect` has not been called.

        :param buf: audio buffer
        :type buf: str
        """
        if not self._decoder:
            return

        # Keep a list of buffers for possible reprocessing later on.
        self._audio_buffers.append(buf)

        # Call the timer callback.
        self.call_timer_callback()

        # Process the audio buffer.
        self._decoder.process_audio(buf)

    def _speech_start_callback(self):
        # Get context info.
        fg_window = Window.get_foreground()
        window_info = {
            "executable": fg_window.executable,
            "title": fg_window.title,
            "handle": fg_window.handle,
        }

        # Call process_begin for all grammars.
        # Note: copy() is used here because process_begin() may load or
        #  unload grammars.
        for wrapper in self._grammar_wrappers.copy().values():
            wrapper.begin_callback(**window_info)

        if not self._mimicking:
            # For performance reasons, trim excess audio buffers from the
            #  start of the list.  Keep a maximum of one second of silence
            #  before speech start was detected.
            chunk = self.config.BUFFER_SIZE
            rate = self.config.RATE
            seconds = 1
            n_buffers = int(rate / chunk * seconds)
            while len(self._audio_buffers) > n_buffers + 1:
                self._audio_buffers.pop(0)

    def _hypothesis_callback(self, hyp):
        """
        Internal Pocket Sphinx hypothesis callback method.

        :param hyp: speech hypothesis
        :rtype: bool
        """
        # Clear any recorded audio buffers.
        self._recorder.clear_buffers()

        # Process the hypothesis.
        processing_occurred = self._process_hypotheses(hyp)

        # Clear audio buffer list because utterance processing has finished.
        while len(self._audio_buffers) > 0:
            self._audio_buffers.pop(0)

        # Ensure that the correct search is used.
        self._set_default_search()

        # Return whether processing occurred, in case this method was called
        #  by mimic().
        return processing_occurred

    def _process_hypotheses(self, hyp):
        """
        Internal method to process speech hypotheses.

        :param hyp: initial speech hypothesis
        :returns: whether processing occurred
        """
        # Create a list of active grammars to process.
        # Include only active exclusive grammars if at least one is active.
        wrappers = []
        exclusive_count = 0
        for wrapper in self._grammar_wrappers.values():
            if wrapper.grammar_is_active: wrappers.append(wrapper)
            if wrapper.exclusive: exclusive_count += 1
        if exclusive_count > 0:
            wrappers = [w for w in wrappers if w.exclusive]

        # No grammar has been loaded.
        if not wrappers: return False

        # Save the given hypothesis for later.  We assume it is the language
        #  model hypothesis.  It can also be a MimickedHypothesis object.
        lm_hypothesis = hyp

        # Get the hypothesis for each active grammar.
        # If this is a regular recognition, switch to each gramar search and
        #  re-process the audio to obtain a closer match.  Otherwise, use
        #  the mimicked words for each grammar's hypothesis.
        hypotheses = {}
        for wrapper in wrappers:
            if not self._mimicking:
                self._set_grammar(wrapper, True)
                hyp = self._decoder.batch_process(self._audio_buffers,
                                                  use_callbacks=False)
                if not hyp: hyp = self._null_hypothesis

            hypotheses[wrapper.search_name] = hyp

        # Get the best hypothesis.
        hyp = self._get_best_hypothesis(hypotheses.values())

        # Initialize a Results object with information about this
        #  recognition.
        # Note: We take a copy of the audio buffer list because it is
        #  emptied after each recognition.
        if self._mimicking:
            audio_buffers = []
            type = "MimicFailure"
        else:
            audio_buffers = [buf for buf in self._audio_buffers]
            type = "Noise"
        results = Results(hyp, type, audio_buffers)

        # If we have a non-null hypothesis, attempt to process it with the
        #  relevant grammars.  Stop on the first grammar that processes the
        #  hypothesis.
        words = results.words()
        result = False
        if words:
            words_rules = self._get_words_rules(words, 0)
            for wrapper in wrappers:
                if hypotheses[wrapper.search_name].hypstr != hyp.hypstr:
                    continue
                rule_names = wrapper.grammar.rule_names
                result = wrapper.process_results(words_rules, rule_names,
                                                 results, True, "Grammar")
                if result: break

        # If no processing has occurred by this point, try to process a
        #  grammar using the LM hypothesis instead, if there is one.
        # Note: This is supposed to work for mimicked recognitions, too.
        if not result and lm_hypothesis.hypstr:
            results.hypothesis = lm_hypothesis
            words = results.words()
            words_rules = self._get_words_rules(words, 1000000)
            for wrapper in wrappers:
                # Allow the LM hypothesis to match *Dictation* elements.
                wrapper.set_dictated_word_guesses(True)
                rule_names = wrapper.grammar.rule_names
                result = wrapper.process_results(words_rules, rule_names,
                                                 results, True,
                                                 "LanguageModel")
                wrapper.set_dictated_word_guesses(False)
                if result: break

        # If no processing has occurred, this is a recognition failure.
        if not result: self.dispatch_recognition_failure(results)

        # Return whether processing occurred.
        return result

    def _get_best_hypothesis(self, hypotheses):
        """
        Take a list of hypotheses and return the most likely one.

        If there was no most likely hypothesis, a null hypothesis is
        returned.

        :param hypotheses: iterable
        :return: Hypothesis object
        """
        # Get all distinct, non-null hypotheses.
        hypotheses = {hyp.hypstr: hyp for hyp in hypotheses
                      if len(hyp.hypstr) > 0}

        # Return early if zero or one distinct hypotheses exist.
        if   len(hypotheses) == 0: return self._null_hypothesis
        elif len(hypotheses) == 1: return hypotheses.popitem()[1]

        # Decide between non-null hypotheses using a Pocket Sphinx search
        #  with each hypothesis as a grammar rule.
        # Note: There is no need to validate words here because each literal
        #  comes from a Pocket Sphinx hypothesis.
        grammar = RootGrammar()
        grammar.language_name = self.language
        i = 0
        for _, hypothesis in hypotheses.items():
            text = hypothesis.hypstr
            grammar.add_rule(PublicRule("rule%d" % i, Literal(text)))
            i += 1
        compiled_jsgf = grammar.compile_grammar()

        # Store the current search name.
        prior_search_name = self._decoder.active_search

        # Set a temporary JSGF search and reprocess the audio.  We should
        #  get a hypothesis.  If we don't, use a null hypothesis.
        self._decoder.end_utterance()
        self._decoder.set_jsgf_string("_temp", _map_to_str(compiled_jsgf))
        self._decoder.active_search = "_temp"
        hyp = self._decoder.batch_process(self._audio_buffers,
                                          use_callbacks=False)
        if not hyp: hyp = self._null_hypothesis

        # Switch back to the previous search and deallocate the temporary
        #  one.
        self._decoder.end_utterance()
        self._decoder.active_search = prior_search_name
        self._decoder.unset_search("_temp")

        # Return the appropriate hypothesis.
        return hypotheses.get(hyp.hypstr, self._null_hypothesis)

    #-----------------------------------------------------------------------
    # Miscellaneous methods.

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        dragonfly.engines.get_speaker().speak(text)

    def _get_language(self):
        return self.config.LANGUAGE


#---------------------------------------------------------------------------


class MimickedHypothesis(object):

    # Note: This class is necessary only because the *pocketsphinx*
    #  Hypothesis class does not accept Unicode hypothesis strings.

    def __init__(self, hypstr, best_score, prob):
        self.hypstr = hypstr
        self.best_score = best_score
        self.prob = prob


class Results(object):
    """ CMU Pocket Sphinx recognition results class. """

    def __init__(self, hypothesis, type, audio_buffers):
        self._hypothesis = hypothesis
        self._type = type
        self._audio_buffers = audio_buffers
        self._grammar = None
        self._rule = None

    def words(self):
        """ Get the words for this recognition. """
        return self._hypothesis.hypstr.split()

    def _set_hypothesis(self, hypothesis):
        assert isinstance(hypothesis, (Hypothesis, MimickedHypothesis))
        self._hypothesis = hypothesis

    hypothesis = property(lambda self: self._hypothesis, _set_hypothesis,
                          doc="The final hypothesis for this recognition.")

    def _set_type(self, type):
        self._type = type

    recognition_type = property(lambda self: self._type, _set_type,
                                doc="The type of this recognition.")

    def _set_grammar(self, grammar):
        self._grammar = grammar

    grammar = property(lambda self: self._grammar, _set_grammar,
                       doc="The grammar which processed this recognition,"
                           " if any.")

    def _set_rule(self, rule):
        self._rule = rule

    rule = property(lambda self: self._rule, _set_rule,
                    doc="The rule that matched this recognition, if any.")

    audio_buffers = property(lambda self: self._audio_buffers,
                             doc="The audio for this recognition, if any.")
