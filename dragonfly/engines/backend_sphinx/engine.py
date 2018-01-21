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

import time
import sys

from jsgf import GrammarError
from jsgf.ext import SequenceRule, DictationGrammar, only_dictation_in_expansion
from pyaudio import PyAudio

import dragonfly.grammar.state as state_
from dragonfly import Grammar, Window
from dragonfly.engines.backend_sphinx import is_engine_available
from dragonfly2jsgf import Translator, LinkedRule
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


class SphinxEngine(EngineBase):
    """Speech recognition engine back-end for CMU Pocket Sphinx."""

    _name = "sphinx"
    DictationContainer = SphinxDictationContainer

    def __init__(self):
        EngineBase.__init__(self)

        try:
            import sphinxwrapper
        except ImportError:
            self._log.error("%s: failed to import sphinxwrapper module." % self)
            raise EngineError("Failed to import the sphinxwrapper module.")

        # Import and set the default configuration module. This can be changed later
        # using the config property.
        import config
        self._config = None
        self.config = config

        # Set other variables
        self._decoder = None
        self._audio_buffers = []
        self.compiler = SphinxJSGFCompiler()
        self._root_grammar = DictationGrammar()
        self._recognition_observer_manager = SphinxRecObsManager(self)
        self._in_progress_sequence_rules = []

        # Recognising loop control variables
        self._recognising = False
        self._recognition_paused = False  # used in pausing/resuming recognition
        self._cancel_recognition_next_time = False
        self._last_recognition_time = None

    @property
    def config(self):
        """
        Python module/object containing engine configuration.
        """
        return self._config

    @config.setter
    def config(self, engine_config):
        # Validate configuration module
        if not (hasattr(engine_config, "DECODER_CONFIG") or
                hasattr(engine_config, "PYAUDIO_STREAM_KEYWORD_ARGS") or
                hasattr(engine_config, "LANGUAGE") or
                hasattr(engine_config, "NEXT_PART_TIMEOUT")):
            EngineError("invalid configuration module")
        self._config = engine_config

    def connect(self):
        """
        Set up the CMU Pocket Sphinx decoder if necessary.
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

        # Set up callback function wrappers
        def hypothesis(hyp):
            # Set speech to the hypothesis string or None if there isn't one
            speech = hyp.hypstr if hyp else None
            return self.hypothesis_callback(speech)

        def speech_start():
            return self.speech_start_callback()

        self._decoder.hypothesis_callback = hypothesis
        self._decoder.speech_start_callback = speech_start

    def _free_engine_resources(self):
        """
        Internal method for freeing the resources used by the engine.
        """
        # Free the decoder and clear the audio buffer list
        self._decoder = None
        self._audio_buffers = []

        # Reset the root grammar
        self._root_grammar = DictationGrammar()
        self._in_progress_sequence_rules = []

    def disconnect(self):
        """
        Free the CMU Sphinx decoder and any other resources used by it.
        """
        # Free resources if the decoder isn't currently being used to recognise,
        # otherwise stop the recognising loop, which will free the resources safely.
        if not self.recognising:
            self._free_engine_resources()
        else:
            self._recognising = False

    # -----------------------------------------------------------------------
    # Methods for working with grammars.

    def _build_grammar_wrapper(self, grammar):
        return GrammarWrapper(grammar, self)

    def _load_root_grammar(self):
        # TODO Ideally this would be called once all grammars load, rather than every time
        # Should be able to do that using a module loader
        if not is_engine_available():
            return

        # Connect to the engine if it isn't connected already and set a Pocket
        # Sphinx JSGF search with the compiled root grammar.
        self.connect()

        # Compile and set the jsgf search. If it compiles to nothing or if there is
        # a GrammarError during compilation, fallback to the dictation search
        # instead.
        try:
            compiled = self._root_grammar.compile_grammar(
                language_name=self.language)
        except GrammarError:
            compiled = ""

        if compiled:
            self._decoder.set_jsgf_string("jsgf", compiled)
            self._set_grammar_search(recompile=False)  # no point recompiling
        else:
            self._set_dictation_search()

    def _set_dictation_search(self):
        """
        Change the active search to the one used for recognising dictation.
        """
        if not self.recognising_dictation:
            self._decoder.end_utterance()  # ensure we're not processing
            self._decoder.active_search = "_default"

    def _set_grammar_search(self, recompile=True):
        """
        Set the JSGF grammar search or the dictation grammar search if there are no
        active JSGF rules.
        :param recompile: whether to recompile the JSGF root grammar.
        """
        # Compile and set the jsgf search. If it compiles to nothing or if there is
        # a GrammarError during compilation, fallback to the dictation search
        # instead.
        if recompile:
            try:
                compiled = self._root_grammar.compile_grammar(
                    language_name=self.language)
            except GrammarError:
                compiled = ""
        else:
            compiled = ""  # doesn't matter, we haven't recompiled

        if compiled or not recompile:
            self._decoder.end_utterance()  # ensure we're not processing
            self._decoder.active_search = "jsgf"
        else:  # fallback to LM
            self._set_dictation_search()

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
        rules = wrapper.jsgf_grammar.rules
        self._root_grammar.add_rules(*rules)
        try:
            self._load_root_grammar()
        except Exception, e:
            self._log.exception("Failed to load grammar %s: %s."
                                % (grammar, e))
        return wrapper

    def _unload_grammar(self, grammar, wrapper):
        """ Unload the given *grammar*. """
        try:
            # Update the root grammar and reload it. Ignore dependent rules
            # in the grammar because all rules are being removed.
            for rule in wrapper.jsgf_grammar.rules:
                self._root_grammar.remove_rule(rule.name,
                                               ignore_dependent=False)
            self._load_root_grammar()
        except Exception, e:
            self._log.exception("Failed to unload grammar %s: %s."
                                % (grammar, e))

    def set_exclusiveness(self, grammar, exclusive):
        try:
            # Not sure what this is, just going to silently ignore it for now
            self._log.debug("set_exclusiveness called for grammar %s. Not doing "
                            "anything yet.")
        except Exception, e:
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
            wrapper.jsgf_grammar.enable_rule(rule.name)
            self._root_grammar.enable_rule(rule.name)
            self._load_root_grammar()
        except Exception, e:
            self._log.exception("Failed to activate grammar %s: %s."
                                % (grammar, e))

    def deactivate_rule(self, rule, grammar):
        self._log.debug("Deactivating rule %s in grammar %s." % (rule.name, grammar.name))
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return
        try:
            wrapper.jsgf_grammar.disable_rule(rule.name)
            self._root_grammar.disable_rule(rule.name)
            self._load_root_grammar()
        except Exception, e:
            self._log.exception("Failed to activate grammar %s: %s."
                                % (grammar, e))

    def update_list(self, lst, grammar):
        wrapper = self._get_grammar_wrapper(grammar)
        name = lst.name
        if not wrapper:
            return

        # Unfortunately there is no way to update lists for Pocket Sphinx without
        # reloading the grammar, so we'll update the list's JSGF rule and reload.

        # Rebuild the list's JSGF rule using dragonfly2jsgf's Translator class
        new_rule = Translator.translate_list(lst)

        # Find the old list rule in the grammar and modify its expansion
        for r in wrapper.jsgf_grammar.rules:
            if r.name == name:
                r.expansion = new_rule.expansion
                break

        # Reload the grammar
        self._load_root_grammar()

    # -----------------------------------------------------------------------
    # Miscellaneous methods.

    @property
    def recognising(self):
        """
        Whether the engine is recognising speech in a loop.
        To stop recognition, use disconnect().
        :return: bool
        """
        return self._recognising

    @property
    def recognising_dictation(self):
        """
        Whether the engine is currently processing speech as dictation.
        :return: bool
        """
        return self._decoder.active_search == "_default"

    def _get_dictation_hypothesis(self, switch_back_afterwards=True):
        """
        Get a dictation hypothesis by reprocessing the audio buffers.
        """
        # Save the current Pocket Sphinx search
        current_search = self._decoder.active_search

        # Switch to the dictation search and reprocess the audio buffers
        self._set_dictation_search()
        dict_hypothesis = self._decoder.batch_process(self._audio_buffers,
                                                      use_callbacks=False)
        if switch_back_afterwards:
            # Switch back to the last search
            self._decoder.end_utterance()
            self._decoder.active_search = current_search
        return dict_hypothesis

    def _get_grammar_wrapper_and_rule(self, rule):
        """
        Get the dragonfly Rule and GrammarWrapper for a JSGF Rule.
        :param rule: JSGF Rule
        :return: tuple
        """
        if isinstance(rule, LinkedRule):
            linked_rule = rule
        else:
            linked_rule = self._root_grammar.get_original_rule(rule)

        df_rule = linked_rule.df_rule
        wrapper = self._get_grammar_wrapper(df_rule.grammar)
        return wrapper, df_rule

    def _handle_recognition_timeout(self):
        """
        Internal method for handling whether the current recognition started too
        late. If it did, this method reprocesses the audio buffers read so far using
        the default search, which might be the dictation (LM) or JSGF search,
        depending on whether there are active JSGF only rules.

        The timeout period is specific to rules containing Dictation elements which
        must be recognised in sequence.
        """
        # If the timeout period is 0 or no SequenceRule is in progress, then there
        # is no timeout.
        next_part_timeout = self.config.NEXT_PART_TIMEOUT
        if not self._in_progress_sequence_rules:
            return

        assert self._last_recognition_time,\
            "SequenceRule is in progress, but there is no recorded last "\
            "recognition time"

        # Check if the next part of the rule wasn't spoken in time.
        current_time = time.time()
        timed_out = current_time >= self._last_recognition_time + next_part_timeout
        if next_part_timeout and timed_out:
            self._log.info("Recognition time-out after %d ms"
                           % (current_time - self._last_recognition_time))

            # I'm not sure if the approach below is quick enough to not interrupt
            # the flow of speech, but this does happen at the beginning of an
            # utterance, so it should be fine, except maybe on slow hardware.

            # Recognition has timed out. Reset sequence rules and start over.
            self._reset_all_sequence_rules()

            # Set the grammar search because only the in-progress rules will be
            # loaded right now, or the search used for dictation.
            # TODO Grammar might need to be reloaded here if the context has changed
            self._set_grammar_search()

            # Setting the grammar search will end the utterance, so we need to
            # process the audio buffers again using batch_process. This will
            # not yield any hypothesis because at this point the user is still
            # speaking.
            self._decoder.batch_process(self._audio_buffers, use_callbacks=False)

        # Set the new last recognition start time
        self._last_recognition_time = current_time

    def speech_start_callback(self):
        # Handle recognition timeout where if speech started too late
        self._handle_recognition_timeout()

        # Notify observers
        self._recognition_observer_manager.notify_begin()

    def hypothesis_callback(self, speech):
        """
        Take a hypothesis string, match it against the JSGF grammar which Pocket
        Sphinx is using, then do whatever the matching Rule implementation does for
        processed recognitions.
        :type speech: str
        """
        matching_rules = []
        if not speech and not self.recognising_dictation:
            # Reprocess as dictation. Don't switch back to the previous search
            # because processing of SequenceRules uses recognising_dictation
            # to handle dictation-only rule parts.
            dict_hyp = self._get_dictation_hypothesis(False)
            speech = dict_hyp.hypstr if dict_hyp else None

        # Handle matching in-progress SequenceRules (if any) or normal rules.
        if speech and self._in_progress_sequence_rules:
            matching_rules = self._handle_in_progress_sequence_rules(speech)
        elif speech:
            matching_rules = self._handle_normal_rules(speech)

        # Clear the internal audio buffer list because it is no longer needed
        self._audio_buffers = []

        if not matching_rules:
            self._recognition_observer_manager.notify_failure()
            self._set_grammar_search()

        # In case this method was called by the mimic method, return the matching
        # rules list for further processing.
        return matching_rules

    def _process_complete_recognition(self, wrapper, words_list):
        """
        Internal method for processing complete recognitions.
        :type wrapper: GrammarWrapper
        :type words_list: list
        """
        # Notify recognition observers
        self._recognition_observer_manager.notify_recognition(words_list)

        # Begin dragonfly processing
        wrapper.process_begin()
        wrapper.process_results(words_list)

        # Clear the in progress list and reset all sequence rules in the grammar.
        self._reset_all_sequence_rules()

        # Switch back to the relevant grammar search (or maybe dictation)
        self._set_grammar_search()

    def _generate_words_list(self, rule, complete_match):
        """
        Generate a words list compatible with dragonfly's processing classes.
        :param rule: JSGF Rule
        :param complete_match: whether all expansions in a SequenceRule must match
        :return: list
        """
        wrapper, df_rule = self._get_grammar_wrapper_and_rule(rule)
        if isinstance(rule, SequenceRule):
            words_list = []
            # Generate a words list using the match values for each expansion in the
            # sequence
            for e in rule.expansion_sequence:
                # Use rule IDs compatible with dragonfly's processing classes
                if only_dictation_in_expansion(e):
                    rule_id = 1000000  # dgndictation id
                else:
                    rule_id = wrapper.grammar.rules.index(df_rule)

                # If the SequenceRule is not completely matched yet and
                # complete_match is False, then use the match values thus far.
                if not complete_match and e.current_match is None:
                    break

                # Get the words from the expansion's current match
                words = e.current_match.split()
                assert words is not None
                for word in words:
                    words_list.append((word, rule_id))
        else:
            rule_id = wrapper.grammar.rules.index(df_rule)
            words_list = [(word, rule_id)
                          for word in rule.expansion.current_match.split()]
        return words_list

    def _handle_normal_rules(self, speech):
        """
        Internal method used by the hypothesis callback for handling normal rules
        that can be spoken in one utterance.
        :return: list
        """
        # No rules will match None or ""
        if not speech:
            return []

        # Find rules of active grammars that match the speech string
        matching_rules = self._root_grammar.find_matching_rules(
            speech, advance_sequence_rules=False)

        for rule in matching_rules:
            if isinstance(rule, SequenceRule):  # spoken in multiple utterances
                if rule.current_is_dictation_only and not \
                        self.recognising_dictation:
                    # Reprocess audio as dictation instead
                    dict_hypothesis = self._get_dictation_hypothesis()

                    # Note: if dict_hypothesis is None, then this recognition was
                    # probably invoked by mimic, so don't invalidate the match.
                    if dict_hypothesis:
                        rule.refuse_matches = False
                        rule.matches(dict_hypothesis.hypstr)

                if rule.has_next_expansion:
                    # TODO Check if other rules have higher probability hypothesises
                    # Go to the next expansion in the sequence and add this rule to
                    # the in progress list
                    rule.set_next()
                    self._in_progress_sequence_rules.append(rule)

                    # Sequence rule is in progress so set the last recognition time
                    # to now.
                    self._last_recognition_time = time.time()

                    # Notify observers
                    self._recognition_observer_manager.notify_next_rule_part(
                        self._generate_words_list(rule, False)
                    )
                else:
                    # The entire sequence has been matched. This rule could only
                    # have had one part to it.
                    self._handle_complete_sequence_rule(rule)
                    break
            else:
                # This rule has been fully recognised. So generate a rule id and
                # words list compatible with dragonfly's processing classes.
                wrapper, df_rule = self._get_grammar_wrapper_and_rule(rule)
                words_list = self._generate_words_list(rule, True)

                # Process the complete recognition and break out of the loop; only
                # one rule should match.
                self._process_complete_recognition(wrapper, words_list)
                break
        return matching_rules

    def _reset_all_sequence_rules(self):
        """
        Internal method for resetting all active SequenceRules and clearing the
        in-progress list.
        """
        for r in self._root_grammar.rules:
            if isinstance(r, SequenceRule):
                r.restart_sequence()

        self._in_progress_sequence_rules = []

    def _handle_in_progress_sequence_rules(self, speech):
        """
        Handle recognising SequenceRules that are in progress.
        Dragonfly processing won't happen in this method until one SequenceRule
        has been matched completely.
        """
        # No rules will match None or ""
        if not speech:
            self._reset_all_sequence_rules()
            return []

        # Sequence rule is in progress so set the last recognition time to now.
        self._last_recognition_time = time.time()

        result = []
        dict_hypothesis = False  # in this case False means unset

        # Process the rules using a shallow copy of the in progress list because the
        # original list will be modified
        notified = False
        for rule in tuple(self._in_progress_sequence_rules):
            # Get a dictation hypothesis if it is required
            if rule.current_is_dictation_only and dict_hypothesis is False and \
                    not self.recognising_dictation:
                dict_hypothesis = self._get_dictation_hypothesis()

            # Match the rule with the appropriate hypothesis string
            if rule.current_is_dictation_only and dict_hypothesis:
                rule.matches(dict_hypothesis.hypstr)
            else:
                rule.matches(speech)

            if not rule.was_matched:
                # Remove and reset the SequenceRule if it didn't match
                rule.restart_sequence()
                self._in_progress_sequence_rules.remove(rule)
            elif rule.has_next_expansion:
                # By calling rule.matches, the speech value was stored as the
                # current expansion's current_match value. Go to the next expansion.
                rule.set_next()
                result.append(rule)

                # Notify with the current recognised words list. Only notify once.
                if not notified:
                    self._recognition_observer_manager.notify_next_rule_part(
                        self._generate_words_list(rule, False)
                    )
                    notified = True
            else:
                # SequenceRule has been completely matched.
                self._handle_complete_sequence_rule(rule)
                result.append(rule)
                # TODO Check if other rules have higher probability hypothesises
                # instead of using the first rule
                break

        # If the list still has rules, then it needs further processing.
        # Load a JSGF Pocket Sphinx search with just the rules in the list, or
        # switch to the dictation search if there are only dictation rules.
        if self._in_progress_sequence_rules:
            temp_grammar = DictationGrammar(rules=self._in_progress_sequence_rules)
            compiled = temp_grammar.compile_grammar(language_name=self.language)
            if not compiled:
                self._set_dictation_search()
            else:
                name = "SeqRulesInProgress"
                self._decoder.set_jsgf_string(name, compiled)
                self._decoder.active_search = name
        return result

    def _handle_complete_sequence_rule(self, rule):
        """
        Handle a SequenceRule that has been completely matched.
        :type rule: SequenceRule
        """
        # Get the GrammarWrapper and dragonfly rule from the SequenceRule
        wrapper, df_rule = self._get_grammar_wrapper_and_rule(rule)
        # Generate a words list
        words_list = self._generate_words_list(rule, True)

        self._process_complete_recognition(wrapper, words_list)

    def recognise_forever(self):
        """
        Start recognising from the default recording device until disconnect() is
        called.

        The pause_recognition or resume_recognition methods can also be called to
        pause and resume without disconnecting and reconnecting.
        """
        # Open a PyAudio stream with the specified keyword args and get the number
        # of frames to read per buffer
        p = PyAudio()
        keyword_args = self.config.PYAUDIO_STREAM_KEYWORD_ARGS
        stream = p.open(**keyword_args)
        frames_per_buffer = keyword_args["frames_per_buffer"]

        # Start recognising in a loop
        stream.start_stream()
        self._recognising = True
        self._cancel_recognition_next_time = False
        while self.recognising:
            # Cancel current recognition if it has been requested
            if self._cancel_recognition_next_time:
                self._decoder.end_utterance()
                self._cancel_recognition_next_time = False

            # Don't read and process audio if recognition has been paused
            if self._recognition_paused:
                time.sleep(0.2)
                continue

            # Read from the audio device (default number of frames is 2048)
            buf = stream.read(frames_per_buffer)

            # Keep a list of AudioData objects for reprocessing with Pocket Sphinx
            # LM search later if the utterance matches no rules.
            self._audio_buffers.append(buf)

            # Process audio and wait a few milliseconds.
            self._decoder.process_audio(buf)

            # This improves the performance; we don't need to process as much audio
            # as the device can read, and people don't speak that fast anyway!
            time.sleep(0.1)

        stream.close()
        self._recognition_paused = False
        self._free_engine_resources()

    def mimic(self, *phrases):
        """
        Mimic a recognition of the given *phrases*.
        Due to the way Dictation elements are processed for this engine, the mimic
        method is implemented to accept variable phrases instead of a list of words.
        """
        # Pretend that Sphinx has started processing speech
        self.speech_start_callback()

        # Process phrases as if they were spoken
        for phrase in phrases:
            result = self.hypothesis_callback(phrase)
            if not result:
                raise MimicFailure("No matching rule found for words %s."
                                   % phrase)

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        # CMU Sphinx speech recognition engines don't come with text-to-speech
        # functionality. For those who need this, the Jasper project has
        # implementations for popular text-to-speech engines:
        # https://github.com/jasperproject/jasper-client
        raise NotImplementedError("text-to-speech is not implemented for this "
                                  "engine")

    def _get_language(self):
        return self.config.LANGUAGE

    # ---------------------------------------------------------------------
    # Recognition loop control methods
    # Stopping recognition loop is done using disconnect()

    def pause_recognition(self):
        """
        If the engine is recognising, stop reading and processing audio from the
        microphone.
        This method should be thread safe.
        """
        self._recognition_paused = True

    def resume_recognition(self):
        """
        If the engine is recognising, resume processing audio from the microphone.
        This method should be thread safe.
        """
        self._recognition_paused = False

    def cancel_recognition(self):
        """
        If a recognition was in progress, cancel it on the next recognise loop
        iteration.
        This method should be thread safe.
        """
        self._cancel_recognition_next_time = True


class GrammarWrapper(object):
    def __init__(self, grammar, engine):
        """
        :type grammar: Grammar
        :type engine: SphinxEngine
        """
        self.grammar = grammar
        self.engine = engine
        self._jsgf_grammar = engine.compiler.compile_grammar(grammar)

    @property
    def jsgf_grammar(self):
        return self._jsgf_grammar

    def process_begin(self):
        """
        Start the dragonfly grammar processing.
        """
        # Get context info for the process_begin method. Dragonfly has a handy
        # static method for this:
        fg_window = Window.get_foreground()
        if sys.platform.startswith("win"):
            process_method = self.grammar.process_begin
        else:
            # Note: get_foreground() is mocked for non-Windows platforms
            # TODO Change to process_begin once cross platform contexts are working
            process_method = self.grammar._process_begin

        # Call the process begin method
        process_method(fg_window.executable, fg_window.title, fg_window.handle)

    def process_results(self, words):
        """
        Start the dragonfly processing of the speech hypothesis.
        :param words: a sequence of (word, rule_id) 2-tuples (pairs)
        """
        SphinxEngine._log.debug("Grammar %s: received recognition %r." %
                                (self.grammar.name, words))

        words_rules = tuple((unicode(w), r) for w, r in words)
        rule_ids = tuple(r for _, r in words_rules)
        words = tuple(w for w, r in words_rules)

        # Call the grammar's general process_recognition method, if present.
        func = getattr(self.grammar, "process_recognition", None)
        if func:
            if not func(words):
                return

        # Iterates through this grammar's rules, attempting to decode each.
        # If successful, call that rule's method for processing the recognition
        # and return.
        s = state_.State(words_rules, rule_ids, self.engine)
        for r in self.grammar.rules:
            # TODO Remove the if windows condition when contexts are working
            if not r.active and sys.platform.startswith("win"):
                continue
            s.initialize_decoding()

            # Iterate each result from decoding state 's' with grammar rule 'r'
            for _ in r.decode(s):
                if s.finished():
                    root = s.build_parse_tree()
                    r.process_recognition(root)
                    return

        SphinxEngine._log.warning("Grammar %s: failed to decode recognition %r."
                                  % (self.grammar.name, words))
