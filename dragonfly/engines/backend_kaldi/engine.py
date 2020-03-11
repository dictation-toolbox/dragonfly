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

import collections, os, subprocess, sys, threading, time

from packaging.version import Version
from six import integer_types, string_types, print_, reraise
from six.moves import zip
import kaldi_active_grammar
from kaldi_active_grammar       import KaldiAgfNNet3Decoder, KaldiError

from ..base                     import (EngineBase, EngineError, MimicFailure,
                                        DelegateTimerManager,
                                        DelegateTimerManagerInterface,
                                        DictationContainerBase)
from .audio                     import MicAudio, VADAudio, AudioStore, WavAudio
from .recobs                    import KaldiRecObsManager
from .testing                   import debug_timer
from dragonfly.grammar.state    import State
from dragonfly.windows          import Window

# Import the Kaldi compiler class. Suppress metaclass TypeErrors raised
# during documentation builds caused by mocking KAG.
try:
    from .compiler                  import KaldiCompiler
except TypeError:
    if os.environ.get("SPHINX_BUILD_RUNNING"):
        KaldiCompiler = None
    else:
        reraise(*sys.exc_info())

#===========================================================================

class KaldiEngine(EngineBase, DelegateTimerManagerInterface):
    """ Speech recognition engine back-end for Kaldi recognizer. """

    _name = "kaldi"
    DictationContainer = DictationContainerBase

    #-----------------------------------------------------------------------

    def __init__(self, model_dir=None, tmp_dir=None,
        input_device_index=None, retain_dir=None, retain_audio=None, retain_metadata=None, vad_aggressiveness=3,
        vad_padding_start_ms=150, vad_padding_end_ms=150, vad_complex_padding_end_ms=500,
        auto_add_to_user_lexicon=True, lazy_compilation=True, invalidate_cache=False,
        alternative_dictation=None, cloud_dictation_lang='en-US',
        ):
        EngineBase.__init__(self)
        DelegateTimerManagerInterface.__init__(self)

        try:
            import kaldi_active_grammar, sounddevice, webrtcvad
        except ImportError as e:
            self._log.error("%s: Failed to import Kaldi engine "
                            "dependencies: %s", self, e)
            raise EngineError("Failed to import Kaldi engine dependencies.")

        # Compatible release version specification
        # https://stackoverflow.com/questions/11887762/how-do-i-compare-version-numbers-in-python/21065570
        with open(os.path.join(os.path.dirname(__file__), 'kag_version.txt')) as file:
            required_kag_version = Version(file.read().strip())
        kag_version = Version(kaldi_active_grammar.__version__)
        if not ((kag_version >= required_kag_version) and (kag_version.release[0:2] == required_kag_version.release[0:2])):
            self._log.error("%s: Incompatible kaldi_active_grammar version %s! Expected ~= %s!" % (self, kag_version, required_kag_version))
            self._log.error("See https://dragonfly2.readthedocs.io/en/latest/kaldi_engine.html#updating-to-a-new-version")
            raise EngineError("Incompatible kaldi_active_grammar version")

        if not (isinstance(retain_dir, string_types) or (retain_dir is None)):
            self._log.error("Invalid retain_dir: %r" % retain_dir)
            retain_dir = None
        if retain_audio and not retain_dir:
            self._log.error("retain_audio=True requires retain_dir to be set; making retain_audio=False instead")
            retain_audio = False

        self._options = dict(
            model_dir = model_dir,
            tmp_dir = tmp_dir,
            input_device_index = input_device_index,
            retain_dir = retain_dir,
            retain_audio = bool(retain_audio) if retain_audio is not None else bool(retain_dir),
            retain_metadata = bool(retain_metadata) if retain_metadata is not None else bool(retain_dir),
            vad_aggressiveness = int(vad_aggressiveness),
            vad_padding_start_ms = int(vad_padding_start_ms),
            vad_padding_end_ms = int(vad_padding_end_ms),
            vad_complex_padding_end_ms = int(vad_complex_padding_end_ms),
            auto_add_to_user_lexicon = bool(auto_add_to_user_lexicon),
            lazy_compilation = bool(lazy_compilation),
            invalidate_cache = bool(invalidate_cache),
            alternative_dictation = alternative_dictation,
            cloud_dictation_lang = cloud_dictation_lang,
        )

        self._compiler = None
        self._decoder = None
        self._audio = None
        self.audio_store = None
        self._recognition_observer_manager = KaldiRecObsManager(self)
        self._timer_manager = DelegateTimerManager(0.02, self)

        self._saving_adaptation_state = False
        self._doing_recognition = False
        self._deferred_disconnect = False

    def connect(self):
        """ Connect to back-end SR engine. """
        if self._decoder:
            return

        self._log.info("Loading Kaldi-Active-Grammar v%s in process %s." % (kaldi_active_grammar.__version__, os.getpid()))
        self._log.info("Kaldi options: %s" % self._options)
        # subprocess.call(['vsjitdebugger', '-p', str(os.getpid())]); time.sleep(5)

        self._compiler = KaldiCompiler(self._options['model_dir'], tmp_dir=self._options['tmp_dir'],
            auto_add_to_user_lexicon=self._options['auto_add_to_user_lexicon'],
            lazy_compilation=self._options['lazy_compilation'],
            alternative_dictation=self._options['alternative_dictation'],
            cloud_dictation_lang=self._options['cloud_dictation_lang'],
            )
        if self._options['invalidate_cache']:
            self._compiler.fst_cache.invalidate()

        top_fst = self._compiler.compile_top_fst()
        dictation_fst_file = self._compiler.dictation_fst_filepath
        self._decoder = KaldiAgfNNet3Decoder(model_dir=self._compiler.model_dir, tmp_dir=self._compiler.tmp_dir,
            top_fst_file=top_fst.filepath, dictation_fst_file=dictation_fst_file, save_adaptation_state=False)
        self._compiler.decoder = self._decoder

        self._audio = VADAudio(aggressiveness=self._options['vad_aggressiveness'], start=False, input_device_index=self._options['input_device_index'])
        self._audio_iter = self._audio.vad_collector(nowait=True,
            start_window_ms=self._options['vad_padding_start_ms'],
            end_window_ms=self._options['vad_padding_end_ms'],
            complex_end_window_ms=self._options['vad_complex_padding_end_ms'],
            )
        self.audio_store = AudioStore(self._audio, maxlen=(1 if self._options['retain_dir'] else 0),
            save_dir=self._options['retain_dir'], save_audio=self._options['retain_audio'], save_metadata=self._options['retain_metadata'])

        self._any_exclusive_grammars = False
        self._in_phrase = False
        self._ignore_current_phrase = False

    def disconnect(self):
        """ Disconnect from back-end SR engine. Exits from ``do_recognition()``. """
        if self._doing_recognition:
            self._deferred_disconnect = True
        else:
            self._deferred_disconnect = False
            if self._audio:
                self._audio.destroy()
                self._audio = None
                self._audio_iter = None
                self.audio_store = None
            self._compiler = None
            self._decoder = None
            self._grammar_wrappers = {}  # From EngineBase

    def print_mic_list(self):
        MicAudio.print_list()

    #-----------------------------------------------------------------------
    # Methods for working with grammars.

    def _load_grammar(self, grammar):
        """ Load the given *grammar*. """
        self._log.info("Loading grammar %s" % grammar.name)
        if not self._decoder:
            self.connect()

        kaldi_rule_by_rule_dict = self._compiler.compile_grammar(grammar, self)
        wrapper = GrammarWrapper(grammar, kaldi_rule_by_rule_dict, self)
        for kaldi_rule in kaldi_rule_by_rule_dict.values():
            kaldi_rule.load(lazy=self._compiler.lazy_compilation)

        return wrapper

    def _unload_grammar(self, grammar, wrapper):
        """ Unload the given *grammar*. """
        self._log.debug("Unloading grammar %s." % grammar.name)
        rules = list(wrapper.kaldi_rule_by_rule_dict.keys())
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
        self._compiler.update_list(lst, grammar)

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
        self._log.debug("Start of mimic: %s" % repr(words))
        try:
            output = words if isinstance(words, string_types) else " ".join(words)
            output = self._compiler.untranslate_output(output)
        except Exception as e:
            raise MimicFailure("Invalid mimic input %r: %s." % (words, e))

        self._recognition_observer_manager.notify_begin()
        kaldi_rules_activity = self._compute_kaldi_rules_activity()
        self.prepare_for_recognition()  # Redundant?

        kaldi_rule, parsed_output = self._parse_recognition(output, mimic=True)
        if not kaldi_rule:
            raise MimicFailure("No matching rule found for %r." % (output,))
        self._log.debug("End of mimic: rule %s, %r" % (kaldi_rule, output))

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        # FIXME
        self._log.warning("Text-to-speech is not implemented for this engine; printing text instead.")
        print_(text)

    def _get_language(self):
        return "en"

    def prepare_for_recognition(self):
        """ Can be called optionally before ``do_recognition()`` to speed up its starting of active recognition. """
        self._compiler.prepare_for_recognition()

    def _do_recognition(self, timeout=None, single=False, audio_iter=None):
        """
            Loops performing recognition, by default forever, or for *timeout* seconds, or for a single recognition if *single=True*.
            Returns ``False`` if timeout occurred without a recognition.
        """
        self._log.debug("do_recognition: timeout %s" % timeout)
        if not self._decoder:
            raise EngineError("Cannot recognize before connect()")
        self._doing_recognition = True

        try:
            self.prepare_for_recognition()

            self._in_phrase = False
            self._ignore_current_phrase = False
            in_complex = False
            timed_out = False

            if timeout != None:
                end_time = time.time() + timeout
                timed_out = True

            if audio_iter == None:
                self._audio.start()
                audio_iter = self._audio_iter
            self._log.info("Listening...")
            next(audio_iter)  # Prime the audio iterator

            # Loop until timeout (if set) or until disconnect() is called.
            while (not self._deferred_disconnect) and ((not timeout) or (time.time() < end_time)):
                self.prepare_for_recognition()
                block = audio_iter.send(in_complex)

                if block is False:
                    # No audio block available
                    time.sleep(0.001)

                elif block is not None:
                    if not self._in_phrase:
                        # Start of phrase
                        self._recognition_observer_manager.notify_begin()
                        with debug_timer(self._log.debug, "computing activity"):
                            kaldi_rules_activity = self._compute_kaldi_rules_activity()
                        self._in_phrase = True
                        self._ignore_current_phrase = False

                    else:
                        # Ongoing phrase
                        kaldi_rules_activity = None
                    self._decoder.decode(block, False, kaldi_rules_activity)
                    if self.audio_store:
                        self.audio_store.add_block(block)
                    output, likelihood = self._decoder.get_output()
                    self._log.log(5, "Partial phrase: likelihood %f, %r [in_complex=%s]", likelihood, output, in_complex)
                    kaldi_rule, words, words_are_dictation, in_dictation = self._compiler.parse_partial_output(output)
                    in_complex = bool(in_dictation or (kaldi_rule and kaldi_rule.is_complex))

                else:
                    # End of phrase
                    self._decoder.decode(b'', True)
                    output, likelihood = self._decoder.get_output()
                    if not self._ignore_current_phrase:
                        # output = self._compiler.untranslate_output(output)
                        kaldi_rule, parsed_output = self._parse_recognition(output)
                        self._log.log(15, "End of phrase: likelihood %f, rule %s, %r" % (likelihood, kaldi_rule, parsed_output))
                        if self._saving_adaptation_state and parsed_output != '':  # Don't save adaptation state for empty recognitions
                            self._decoder.save_adaptation_state()
                        if self.audio_store:
                            if kaldi_rule and parsed_output != '':  # Don't store audio/metadata for empty recognitions
                                self.audio_store.finalize(parsed_output,
                                    kaldi_rule.parent_grammar.name, kaldi_rule.parent_rule.name,
                                    likelihood=likelihood, has_dictation=kaldi_rule.has_dictation)
                            else:
                                self.audio_store.cancel()

                    self._in_phrase = False
                    self._ignore_current_phrase = False
                    in_complex = False
                    timed_out = False
                    if single:
                        break

                self.call_timer_callback()

        except StopIteration:
            if audio_iter == self._audio_iter:
                self._log.warning("audio iterator stopped unexpectedly")

        finally:
            self._doing_recognition = False
            if audio_iter == self._audio_iter and self._audio:
                self._audio.stop()
            if self.audio_store:
                self.audio_store.save_all()

        return not timed_out

    in_phrase = property(lambda self: self._in_phrase,
        doc="Whether or not the engine is currently in the middle of hearing a phrase from the user.")

    def recognize_wave_file(self, filename, **kwargs):
        """ Does recognition on given wave file, treating it as a single utterance (without VAD), then returns. """
        self.do_recognition(audio_iter=WavAudio.read_file(filename), **kwargs)

    def ignore_current_phrase(self):
        """
            Marks the current phrase's recognition to be ignored when it completes, or does nothing if there is none.
            Returns *bool* indicating whether or not there was a current phrase being heard.
        """
        if not self.in_phrase:
            return False
        self._ignore_current_phrase = True
        return True

    saving_adaptation_state = property(lambda self: self._saving_adaptation_state,
        doc="Whether or not the engine is currently automatically saving adaptation state between utterances.")
    @saving_adaptation_state.setter
    def saving_adaptation_state(self, value):
        self._saving_adaptation_state = value

    def start_saving_adaptation_state(self):
        """ Enable automatic saving of adaptation state between utterances, which may improve recognition accuracy in the short term, but is not stored between runs. """
        self.saving_adaptation_state = True

    def stop_saving_adaptation_state(self):
        """ Disables automatic saving of adaptation state between utterances, which you might want to do when you expect there to be noise and don't want it to pollute your current adaptation state. """
        self.saving_adaptation_state = False

    def reset_adaptation_state(self):
        self._decoder.reset_adaptation_state()

    #-----------------------------------------------------------------------
    # Internal processing methods.

    def _iter_all_grammar_wrappers_dynamically(self):
        """ Accounts for grammar wrappers being dynamically added during iteration. """
        processed_grammar_wrappers = set()
        todo_grammar_wrappers = set(self._grammar_wrappers.values())
        while todo_grammar_wrappers:
            while todo_grammar_wrappers:
                grammar_wrapper = todo_grammar_wrappers.pop()
                yield grammar_wrapper
                processed_grammar_wrappers.add(grammar_wrapper)
            todo_grammar_wrappers = set(self._grammar_wrappers.values()) - processed_grammar_wrappers

    def _compute_kaldi_rules_activity(self, phrase_start=True):
        if phrase_start:
            fg_window = Window.get_foreground()
            for grammar_wrapper in self._iter_all_grammar_wrappers_dynamically():
                grammar_wrapper.phrase_start_callback(fg_window)
        self.prepare_for_recognition()
        self._active_kaldi_rules = set()
        self._kaldi_rules_activity = [False] * self._compiler.num_kaldi_rules
        for grammar_wrapper in self._iter_all_grammar_wrappers_dynamically():
            if grammar_wrapper.active and (not self._any_exclusive_grammars or (self._any_exclusive_grammars and grammar_wrapper.exclusive)):
                for kaldi_rule in grammar_wrapper.kaldi_rule_by_rule_dict.values():
                    if kaldi_rule.active:
                        self._active_kaldi_rules.add(kaldi_rule)
                        self._kaldi_rules_activity[kaldi_rule.id] = True
        self._log.debug("active kaldi_rules: %s", [kr.name for kr in self._active_kaldi_rules])
        return self._kaldi_rules_activity

    def _parse_recognition(self, output, mimic=False):
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

            if self._log.isEnabledFor(12):
                try:
                    self._log.log(12, "Alignment (word,time,length): %s" % self._decoder.get_word_align(output))
                except KaldiError as e:
                    self._log.warning("Exception logging word alignment")

        else:
            raise EngineError("Invalid _compiler.parsing_framework")

        words = tuple(words)
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
                    self.engine._recognition_observer_manager.notify_recognition(words, rule, root)
                    with debug_timer(self.engine._log.debug, "rule execution time"):
                        rule.process_recognition(root)
                    self.engine._recognition_observer_manager.notify_post_recognition(words, rule, root)
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
