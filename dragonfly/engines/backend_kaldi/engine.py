#
# This file is part of Dragonfly.
# (c) Copyright 2019 by David Zurow
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
Kaldi engine classes
"""

import collections, os, subprocess, threading, time

from six import string_types, integer_types, print_

from ..base                     import (EngineBase, EngineError, MimicFailure,
                                        DelegateTimerManager, DelegateTimerManagerInterface, DictationContainerBase)
from .recobs                    import KaldiRecObsManager
from .testing                   import debug_timer
from ...grammar.state           import State
from ...windows                 import Window

try:
    from kaldi_active_grammar       import KaldiAgfNNet3Decoder, KaldiError
    from .compiler                  import KaldiCompiler
    from .audio                     import MicAudio, VADAudio, AudioStore
    ENGINE_AVAILABLE = True
except ImportError:
    # Import a few things here optionally for readability (the engine won't
    # start without them) and so that autodoc can import this module without
    # them.
    ENGINE_AVAILABLE = False



#===========================================================================

class KaldiEngine(EngineBase, DelegateTimerManagerInterface):
    """ Speech recognition engine back-end for Kaldi recognizer. """

    _name = "kaldi"
    DictationContainer = DictationContainerBase

    #-----------------------------------------------------------------------

    def __init__(self, model_dir=None, tmp_dir=None,
        vad_aggressiveness=None, vad_padding_ms=None, input_device_index=None,
        auto_add_to_user_lexicon=None,
        cloud_dictation=None,  # FIXME: cloud_dictation_lang
        ):
        EngineBase.__init__(self)
        DelegateTimerManagerInterface.__init__(self)

        if not ENGINE_AVAILABLE:
            self._log.error("%s: Failed to import Kaldi engine dependencies. Are they installed?" % self)
            raise EngineError("Failed to import Kaldi engine dependencies.")

        self._model_dir = model_dir if model_dir is not None else 'kaldi_model_zamia'
        self._tmp_dir = tmp_dir if tmp_dir is not None else 'kaldi_tmp'
        self._vad_aggressiveness = vad_aggressiveness if vad_aggressiveness is not None else 3
        self._vad_padding_ms = vad_padding_ms if vad_padding_ms is not None else 300
        self._input_device_index = input_device_index
        self._auto_add_to_user_lexicon = auto_add_to_user_lexicon
        self._cloud_dictation = cloud_dictation

        self._compiler = None
        self._decoder = None
        self._audio = None
        self._recognition_observer_manager = KaldiRecObsManager(self)
        self._timer_manager = DelegateTimerManager(0.02, self)

    def connect(self):
        """ Connect to back-end SR engine. """
        if self._decoder:
            return

        self._log.debug("Loading KaldiEngine in process %s." % os.getpid())
        # subprocess.call(['vsjitdebugger', '-p', str(os.getpid())]); time.sleep(5)

        self._compiler = KaldiCompiler(self._model_dir, tmp_dir=self._tmp_dir, auto_add_to_user_lexicon=self._auto_add_to_user_lexicon, cloud_dictation=self._cloud_dictation)
        # self._compiler.fst_cache.invalidate()

        top_fst = self._compiler.compile_top_fst()
        dictation_fst_file = self._compiler.dictation_fst_filepath
        self._decoder = KaldiAgfNNet3Decoder(model_dir=self._model_dir, tmp_dir=self._tmp_dir, top_fst_file=top_fst.filepath, dictation_fst_file=dictation_fst_file)
        self._compiler.decoder = self._decoder

        self._audio = VADAudio(aggressiveness=self._vad_aggressiveness, start=False, input_device_index=self._input_device_index)
        self._audio_iter = self._audio.vad_collector(padding_ms=self._vad_padding_ms, nowait=True)
        self.audio_store = AudioStore(self._audio, maxlen=0)

        self._any_exclusive_grammars = False

    def disconnect(self):
        """ Disconnect from back-end SR engine. """
        self._audio.destroy()
        self._audio = None
        self._compiler = None
        self._decoder = None

    def print_mic_list(self):
        MicAudio.print_list()

    #-----------------------------------------------------------------------
    # Methods for working with grammars.

    def _load_grammar(self, grammar):
        """ Load the given *grammar*. """
        self._log.info("Loading grammar %s..." % grammar.name)
        if not self._decoder:
            self.connect()
        grammar.engine = self

        # Dependency checking.
        memo = []
        for r in grammar._rules:
            for d in r.dependencies(memo):
                grammar.add_dependency(d)

        kaldi_rule_by_rule_dict = self._compiler.compile_grammar(grammar, self)
        wrapper = GrammarWrapper(grammar, kaldi_rule_by_rule_dict, self)
        for kaldi_rule in kaldi_rule_by_rule_dict.values():
            kaldi_rule.load_fst()

        self._log.info("...Done loading grammar %s." % grammar.name)
        return wrapper

    def _unload_grammar(self, grammar, wrapper):
        """ Unload the given *grammar*. """
        self._log.debug("Unloading grammar %s." % grammar.name)
        rules = wrapper.kaldi_rule_by_rule_dict.keys()
        self._compiler.unload_grammar(grammar, rules, self)

    def activate_grammar(self, grammar):
        """ Activate the given *grammar*. """
        self._log.debug("Activating grammar %s." % grammar.name)
        self._get_grammar_wrapper(grammar).active = True

    def deactivate_grammar(self, grammar):
        """ Deactivate the given *grammar*. """
        self._log.debug("Deactivating grammar %s." % grammar.name)
        self._get_grammar_wrapper(grammar).active = False

    def activate_rule(self, rule, grammar):
        """ Activate the given *rule*. """
        self._log.debug("Activating rule %s in grammar %s." % (rule.name, grammar.name))
        self._compiler.kaldi_rule_by_rule_dict[rule].active = True

    def deactivate_rule(self, rule, grammar):
        """ Deactivate the given *rule*. """
        self._log.debug("Deactivating rule %s in grammar %s." % (rule.name, grammar.name))
        self._compiler.kaldi_rule_by_rule_dict[rule].active = False

    def update_list(self, lst, grammar):
        wrapper = self._get_grammar_wrapper(grammar)
        rules = wrapper.kaldi_rule_by_rule_dict.keys()
        self._compiler.update_list(lst, rules, grammar)

    def set_exclusiveness(self, grammar, exclusive):
        self._log.debug("Setting exclusiveness of grammar %s to %s." % (grammar.name, exclusive))
        self._get_grammar_wrapper(grammar).exclusive = exclusive
        if exclusive:
            self._get_grammar_wrapper(grammar).active = True
        self._any_exclusive_grammars = any(gw.exclusive for gw in self._grammar_wrappers.values())

    #-----------------------------------------------------------------------
    # Miscellaneous methods.

    def mimic(self, words):
        """ Mimic a recognition of the given *words*. """
        self._log.debug("Start of mimic: %r" % words)
        try:
            output = words if isinstance(words, string_types) else " ".join(words)
            output = self._compiler.untranslate_output(output)
        except Exception as e:
            raise MimicFailure("Invalid mimic input %r: %s." % (words, e))

        self._recognition_observer_manager.notify_begin()
        kaldi_rules_activity = self._compute_kaldi_rules_activity()

        kaldi_rule, parsed_output = self._parse_recognition(output, mimic=True)
        if not kaldi_rule:
            raise MimicFailure("No matching rule found for words %r." % (parsed_output,))
        self._log.debug("End of mimic: rule %s, %r" % (kaldi_rule, output))

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        # FIXME
        self._log.warning("Text-to-speech is not implemented for this engine; printing text instead.")
        print_(text)

    def _get_language(self):
        return "en"

    def do_recognition(self, timeout=None, single=False):
        self._log.debug("do_recognition: timeout %s" % timeout)

        self._prepare_for_recognition()

        if timeout != None:
            end_time = time.time() + timeout
            timed_out = True
        phrase_started = False

        self._audio.start()

        try:
            while (not timeout) or (time.time() < end_time):
                block = next(self._audio_iter)

                if block is False:
                    # No audio block available
                    time.sleep(0.001)

                elif block is not None:
                    if not phrase_started:
                        # Start of phrase
                        self._recognition_observer_manager.notify_begin()
                        with debug_timer(self._log.debug, "computing activity"):
                            kaldi_rules_activity = self._compute_kaldi_rules_activity()
                        phrase_started = True
                    else:
                        # Ongoing phrase
                        kaldi_rules_activity = None
                    self._decoder.decode(block, False, kaldi_rules_activity)
                    if self.audio_store:
                        self.audio_store.add_block(block)

                else:
                    # End of phrase
                    self._decoder.decode('', True)
                    output, likelihood = self._decoder.get_output()
                    output = self._compiler.untranslate_output(output)
                    kaldi_rule, parsed_output = self._parse_recognition(output)
                    self._log.debug("End of utterence: likelihood %f, rule %s, %r" % (likelihood, kaldi_rule, parsed_output))
                    if self.audio_store and kaldi_rule:
                        self.audio_store.finalize(parsed_output, kaldi_rule.parent_grammar.name, kaldi_rule.parent_rule.name)
                    phrase_started = False
                    timed_out = False
                    if single:
                        break

                self.call_timer_callback()

        finally:
            self._audio.stop()

        return not timed_out

    def wait_for_recognition(self, timeout=None):
        return self.do_recognition(timeout=timeout, single=True)

    saving_adaptation_state = property(lambda self: self._decoder.saving_adaptation_state, doc="FIXME")

    def start_saving_adaptation_state(self):
        self._decoder.saving_adaptation_state = True

    def stop_saving_adaptation_state(self):
        self._decoder.saving_adaptation_state = False

    def reset_adaptation_state(self):
        self._decoder.reset_adaptation_state()

    #-----------------------------------------------------------------------
    # Internal processing methods.

    def _prepare_for_recognition(self):
        self._compiler.prepare_for_recognition()

    def _compute_kaldi_rules_activity(self, phrase_start=True):
        self._active_kaldi_rules = []
        self._kaldi_rules_activity = [False] * self._compiler.num_kaldi_rules
        fg_window = Window.get_foreground()
        for grammar_wrapper in self._grammar_wrappers.values():
            if phrase_start:
                grammar_wrapper.phrase_start_callback(fg_window)
            if grammar_wrapper.active and (not self._any_exclusive_grammars or (self._any_exclusive_grammars and grammar_wrapper.exclusive)):
                for kaldi_rule in grammar_wrapper.kaldi_rule_by_rule_dict.values():
                    if kaldi_rule.active:
                        self._active_kaldi_rules.append(kaldi_rule)
                        self._kaldi_rules_activity[kaldi_rule.id] = True
        self._log.debug("active kaldi_rules: %s", [kr.name for kr in self._active_kaldi_rules])
        return self._kaldi_rules_activity

    def _parse_recognition(self, output, mimic=False):
        # if output == '':
        #     self._log.warning("attempted to parse empty recognition")
        #     return None

        if mimic or self._compiler.parsing_framework == 'text':
            with debug_timer(self._log.debug, "kaldi_rule parse time"):
                detect_ambiguity = False
                results = []
                for kaldi_rule in sorted(self._active_kaldi_rules, key=lambda kr: 100 if kr.has_dictation else 0):
                    self._log.debug("attempting to parse %r with %s", output, kaldi_rule)
                    words = self._compiler.parse_output_for_rule(kaldi_rule, output)
                    if words is None:
                        continue
                    # self._log.debug("success %d", kaldi_rule_id)
                    # Pass (kaldi_rule, words) to below.
                    results.append((kaldi_rule, words))
                    if not detect_ambiguity:
                        break

                if not results:
                    if not mimic:
                        # We should never receive an unparsable recognition from kaldi, only from mimic
                        self._log.error("unable to parse recognition: %r" % output)
                    self._recognition_observer_manager.notify_failure()
                    return None, ''
                if len(results) > 1:
                    self._log.warning("ambiguity in recognition: %r" % output)
                    # FIXME: improve sorting criterion
                    results.sort(key=lambda result: 100 if result[0].has_dictation else 0)

                kaldi_rule, words = results[0]
                words_are_dictation = [True] * len(words)  # FIXME: hack, but seems to work fine? only a problem for ambiguous rules containing dictation, which should be handled above

        elif self._compiler.parsing_framework == 'token':
            kaldi_rule, words, words_are_dictation = self._compiler.parse_output(output,
                dictation_info_func=lambda: (self.audio_store.current_audio_data, self._decoder.get_word_align(output)))
            if kaldi_rule is None:
                if words != []:
                    # We should never receive an unparsable recognition from kaldi, unless it's empty (from noise)
                    self._log.error("unable to parse recognition: %r" % output)
                self._recognition_observer_manager.notify_failure()
                return None, ''

        else:
            raise EngineError("invalid _compiler.parsing_framework")

        self._recognition_observer_manager.notify_recognition(words)
        grammar_wrapper = self._get_grammar_wrapper(kaldi_rule.parent_grammar)
        with debug_timer(self._log.debug, "dragonfly parse time"):
            grammar_wrapper.recognition_callback(words, kaldi_rule.parent_rule, words_are_dictation)

        parsed_output = ' '.join(words)
        return kaldi_rule, parsed_output


#===========================================================================

class GrammarWrapper(object):

    def __init__(self, grammar, kaldi_rule_by_rule_dict, engine):
        self.grammar = grammar
        self.kaldi_rule_by_rule_dict = kaldi_rule_by_rule_dict
        self.engine = engine

        self.active = True
        self.exclusive = False

    def phrase_start_callback(self, fg_window):
        self.grammar.process_begin(fg_window.executable, fg_window.title, fg_window.handle)

    def recognition_callback(self, words, rule, words_are_dictation):
        try:
            # Prepare the words and rule names for the element parsers
            rule_names = (rule.name,) + (('dgndictation',) if any(words_are_dictation) else ())
            words_rules = tuple((word, 0 if not is_dictation else 1)
                for (word, is_dictation) in zip(words, words_are_dictation))

            # Attempt to parse the recognition
            func = getattr(self.grammar, "process_recognition", None)
            if func:
                if not func(words):
                    return

            state = State(words_rules, rule_names, self.engine)
            state.initialize_decoding()
            for result in rule.decode(state):
                if state.finished():
                    root = state.build_parse_tree()
                    with debug_timer(self.engine._log.debug, "rule execution time"):
                        rule.process_recognition(root)
                    return

        except Exception as e:
            self.engine._log.error("Grammar %s: exception: %s" % (self.grammar._name, e), exc_info=True)

        # If this point is reached, then the recognition was not processed successfully
        self.engine._log.error("Grammar %s: failed to decode rule %s recognition %r." % (self.grammar._name, rule.name, words))

    # FIXME
    # def recognition_other_callback(self, StreamNumber, StreamPosition):
    #         func = getattr(self.grammar, "process_recognition_other", None)
    #         if func:
    #             func(words=False)
    #         return

    # FIXME
    # def recognition_failure_callback(self, StreamNumber, StreamPosition, Result):
    #         func = getattr(self.grammar, "process_recognition_failure", None)
    #         if func:
    #             func()
    #         return
