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

import collections, logging, os, sys, time

from packaging.version import Version
from six import string_types, print_, reraise
from six.moves import zip
import kaldi_active_grammar
from kaldi_active_grammar       import KaldiError, KaldiRule

from ..base                     import (EngineBase,
                                        EngineError,
                                        MimicFailure,
                                        DelegateTimerManager,
                                        DelegateTimerManagerInterface,
                                        DictationContainerBase,
                                        GrammarWrapperBase)
from .audio                     import MicAudio, VADAudio, AudioStore, WavAudio
from .dictation                 import user_dictation_list, user_dictation_dictlist
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

nan = float('nan')

#===========================================================================

class KaldiEngine(EngineBase, DelegateTimerManagerInterface):
    """ Speech recognition engine back-end for Kaldi recognizer. """

    _name = "kaldi"
    DictationContainer = DictationContainerBase
    _required_kag_version = "2.1.0"

    #-----------------------------------------------------------------------

    def __init__(self, model_dir=None, tmp_dir=None, input_device_index=None,
        audio_input_device=None, audio_self_threaded=True, audio_auto_reconnect=True, audio_reconnect_callback=None,
        retain_dir=None, retain_audio=None, retain_metadata=None, retain_approval_func=None,
        vad_aggressiveness=3, vad_padding_start_ms=150, vad_padding_end_ms=200, vad_complex_padding_end_ms=600,
        auto_add_to_user_lexicon=False, lazy_compilation=True, invalidate_cache=False,
        expected_error_rate_threshold=None,
        alternative_dictation=None,
        compiler_init_config=None, decoder_init_config=None,
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
        required_kag_version = Version(self._required_kag_version)
        kag_version = Version(kaldi_active_grammar.__version__)
        if not ((kag_version >= required_kag_version) and (kag_version.release[0:2] == required_kag_version.release[0:2])):
            self._log.error("%s: Incompatible kaldi_active_grammar version %s! Expected ~= %s!" % (self, kag_version, required_kag_version))
            self._log.error("See https://dragonfly2.readthedocs.io/en/latest/kaldi_engine.html#updating-to-a-new-version")
            if not os.environ.get('DRAGONFLY_DEVELOP'):
                raise EngineError("Incompatible kaldi_active_grammar version")

        # Handle engine parameters
        if input_device_index is not None:
            if audio_input_device is not None:
                raise ValueError("Cannot set both input_device_index and audio_input_device")
            self._log.warning("%s: input_device_index is deprecated; please use audio_input_device", self)
            audio_input_device = int(input_device_index)
        if audio_input_device not in (None, False) and not isinstance(audio_input_device, (int, string_types)):
            raise TypeError("Invalid audio_input_device not int or string: %r" % (audio_input_device,))
        if audio_reconnect_callback is not None and not callable(audio_reconnect_callback):
            raise TypeError("Invalid audio_reconnect_callback not callable: %r" % (audio_reconnect_callback,))
        if retain_dir is not None and not isinstance(retain_dir, string_types):
            raise TypeError("Invalid retain_dir not string: %r" % (retain_dir,))
        if retain_audio and not retain_dir:
            raise ValueError("retain_audio=True requires retain_dir to be set")
        if retain_approval_func is not None and not callable(retain_approval_func):
            raise TypeError("Invalid retain_approval_func not callable: %r" % (retain_approval_func,))

        self._options = dict(
            model_dir = model_dir,
            tmp_dir = tmp_dir,
            audio_input_device = audio_input_device,
            audio_self_threaded = bool(audio_self_threaded),
            audio_auto_reconnect = bool(audio_auto_reconnect),
            audio_reconnect_callback = audio_reconnect_callback,
            retain_dir = retain_dir,
            retain_audio = bool(retain_audio) if retain_audio is not None else bool(retain_dir),
            retain_metadata = bool(retain_metadata) if retain_metadata is not None else bool(retain_dir),
            retain_approval_func = retain_approval_func,
            vad_aggressiveness = int(vad_aggressiveness),
            vad_padding_start_ms = int(vad_padding_start_ms),
            vad_padding_end_ms = int(vad_padding_end_ms),
            vad_complex_padding_end_ms = int(vad_complex_padding_end_ms),
            auto_add_to_user_lexicon = bool(auto_add_to_user_lexicon),
            lazy_compilation = bool(lazy_compilation),
            invalidate_cache = bool(invalidate_cache),
            expected_error_rate_threshold = float(expected_error_rate_threshold) if expected_error_rate_threshold is not None else None,
            alternative_dictation = alternative_dictation,
            compiler_init_config = dict(compiler_init_config) if compiler_init_config else {},
            decoder_init_config = dict(decoder_init_config) if decoder_init_config else {},
        )

        # Setup
        self._reset_state()
        self._recognition_observer_manager = KaldiRecObsManager(self)
        self._timer_manager = DelegateTimerManager(0.02, self)

    def _reset_state(self):
        self._compiler = None
        self._decoder = None
        self._audio = None
        self._audio_iter = None
        self.audio_store = None

        self._loadunload_queue = collections.deque()
        self._grammar_wrappers_copy = {}
        self._any_exclusive_grammars = False
        self._saving_adaptation_state = False
        self._ignore_current_phrase = False
        self._in_phrase = False
        self._doing_recognition = False
        self._deferred_disconnect = False

    def connect(self):
        """ Connect to back-end SR engine. """
        if self._decoder:
            return
        self._reset_state()

        self._log.info("Loading Kaldi-Active-Grammar v%s in process %s." % (kaldi_active_grammar.__version__, os.getpid()))
        self._log.info("Kaldi options: %s" % self._options)

        self._compiler = KaldiCompiler(self._options['model_dir'], tmp_dir=self._options['tmp_dir'],
            auto_add_to_user_lexicon=self._options['auto_add_to_user_lexicon'],
            lazy_compilation=self._options['lazy_compilation'],
            alternative_dictation=self._options['alternative_dictation'],
            **self._options['compiler_init_config']
            )
        if self._options['invalidate_cache']:
            self._compiler.fst_cache.invalidate()

        self._decoder = self._compiler.init_decoder(config=self._options['decoder_init_config'])

        if self._options['audio_input_device'] is not False:
            self._audio = VADAudio(
                aggressiveness=self._options['vad_aggressiveness'],
                start=False,
                input_device=self._options['audio_input_device'],
                self_threaded=self._options['audio_self_threaded'],
                reconnect_callback=self._options['audio_reconnect_callback'],
                )
            self._audio_iter = self._audio.vad_collector(nowait=True,
                audio_auto_reconnect=self._options['audio_auto_reconnect'],
                start_window_ms=self._options['vad_padding_start_ms'],
                end_window_ms=self._options['vad_padding_end_ms'],
                complex_end_window_ms=self._options['vad_complex_padding_end_ms'],
                )
            self.audio_store = AudioStore(self._audio, maxlen=(1 if self._options['retain_dir'] else 0),
                save_dir=self._options['retain_dir'], save_audio=self._options['retain_audio'], save_metadata=self._options['retain_metadata'],
                retain_approval_func=self._options['retain_approval_func'])

    def disconnect(self):
        """ Disconnect from back-end SR engine. Exits from ``do_recognition()``. """
        if self._doing_recognition:
            self._deferred_disconnect = True
        else:
            if self._audio:
                self._audio.destroy()
            if self.audio_store:
                self.audio_store.save_all()
            self._reset_state()
            self._grammar_wrappers = {}  # From EngineBase

    @staticmethod
    def print_mic_list():
        MicAudio.print_list()

    def _apply_win32_kb_input_logging_fix(self):
        # Hack to avoid bug processing keyboard actions on Windows
        if os.name == 'nt':
            action_exec_logger = logging.getLogger('action.exec')
            if action_exec_logger.getEffectiveLevel() > logging.DEBUG:
                self._log.warning("%s: Enabling logging of actions "
                                  "execution to avoid bug processing "
                                  "keyboard actions on Windows", self)
                action_exec_logger.setLevel(logging.DEBUG)

    #-----------------------------------------------------------------------
    # Methods for working with grammars.

    def _load_grammar(self, grammar):
        """ Load the given *grammar*. """
        if not self._decoder:
            self.connect()

        self._log.info("Loading grammar %s" % grammar.name)
        kaldi_rule_by_rule_dict = self._compiler.compile_grammar(grammar, self)
        wrapper = GrammarWrapper(grammar, kaldi_rule_by_rule_dict, self,
                                 self._recognition_observer_manager)

        def load():
            for (rule, kaldi_rule) in kaldi_rule_by_rule_dict.items():
                kaldi_rule.active = bool(rule.active)  # Initialize to correct activity
                kaldi_rule.load(lazy=self._compiler.lazy_compilation)
        if self._in_phrase:
            self._loadunload_queue.append(load)
        else:
            load()

        return wrapper

    def _unload_grammar(self, grammar, wrapper):
        """ Unload the given *grammar*. """
        self._log.debug("Unloading grammar %s." % grammar.name)
        def unload():
            rules = list(wrapper.kaldi_rule_by_rule_dict.keys())
            self._compiler.unload_grammar(grammar, rules, self)
        if self._in_phrase:
            self._loadunload_queue.append(unload)
        else:
            unload()

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

        recognition = self._parse_recognition(output, mimic=True)
        if not recognition.kaldi_rule:
            recognition.fail(mimic=True)
            raise MimicFailure("No matching rule found for %r." % (output,))
        recognition.process(mimic=True)
        self._log.debug("End of mimic: rule %s, %r" % (recognition.kaldi_rule, output))
        if not self._log.isEnabledFor(10):
            self._log.log(15, "End of mimic: rule %s, %r" % (recognition.kaldi_rule, output))

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        # FIXME
        self._log.warning("Text-to-speech is not implemented for this engine; printing text instead.")
        print_(text)

    def _get_language(self):
        return "en"

    def _has_quoted_words_support(self):
        return False

    def prepare_for_recognition(self):
        """ Can be called optionally before ``do_recognition()`` to speed up its starting of active recognition. """
        if self._in_phrase:
            self._log.warning("prepare_for_recognition ignored while in phrase; will be run after")
            return
        try:
            while self._loadunload_queue:
                operation = self._loadunload_queue.popleft()
                operation()
            self._compiler.prepare_for_recognition()
        except KaldiError as e:
            if len(e.args) >= 2 and isinstance(e.args[1], KaldiRule):
                kaldi_rule = e.args[1]
                raise self._compiler.make_compiler_error_for_kaldi_rule(kaldi_rule)
            raise

    def _do_recognition(self, timeout=None, single=False, audio_iter=None):
        """
            Loops performing recognition, by default forever, or for *timeout* seconds, or for a single recognition if *single=True*.
            Returns ``False`` if timeout occurred without a recognition.
        """
        self._log.debug("do_recognition: timeout %s" % timeout)
        if not self._decoder:
            raise EngineError("Cannot recognize before connect()")
        if audio_iter is None and self._audio is None:
            raise EngineError("No audio input")
        self._doing_recognition = True
        self._in_phrase = False
        self._ignore_current_phrase = False
        in_complex = False
        end_time = None
        timed_out = False

        try:
            self.prepare_for_recognition()  # Try to get compilation out of the way before starting audio

            if timeout != None:
                end_time = time.time() + timeout
                timed_out = True

            if audio_iter == None:
                self._audio.start()
                audio_iter = self._audio_iter
            self._log.info("Listening...")
            next(audio_iter)  # Prime the audio iterator

            # Loop until timeout (if set) or until disconnect() is called.
            while (not self._deferred_disconnect) and ((not end_time) or (time.time() < end_time)):
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
                        self._grammar_wrappers_copy = self._grammar_wrappers.copy()  # Keep a copy of valid grammar wrappers as of the start of utterance

                    else:
                        # Ongoing phrase
                        kaldi_rules_activity = None
                    self._decoder.decode(block, False, kaldi_rules_activity)
                    if self.audio_store:
                        self.audio_store.add_block(block)
                    output, info = self._decoder.get_output()
                    self._log.log(5, "Partial phrase: %r [in_complex=%s]", output, in_complex)
                    kaldi_rule, words, words_are_dictation_mask, in_dictation = self._compiler.parse_partial_output(output)
                    in_complex = bool(in_dictation or (kaldi_rule and kaldi_rule.is_complex))

                else:
                    # End of phrase
                    self._decoder.decode(b'', True)
                    output, info = self._decoder.get_output()
                    if not self._ignore_current_phrase:
                        expected_error_rate = info.get('expected_error_rate', nan)
                        confidence = info.get('confidence', nan)
                        # output = self._compiler.untranslate_output(output)
                        recognition = self._parse_recognition(output)
                        is_acceptable_recognition = recognition.kaldi_rule and (recognition.has_dictation or not (
                            self._options['expected_error_rate_threshold'] and (expected_error_rate > self._options['expected_error_rate_threshold'])
                        ))
                        if is_acceptable_recognition:
                            recognition.process(expected_error_rate=expected_error_rate, confidence=confidence)
                        else:
                            recognition.fail(expected_error_rate=expected_error_rate, confidence=confidence)

                        kaldi_rule, parsed_output = recognition.kaldi_rule, recognition.parsed_output
                        self._log.log(15, "End of phrase: eer=%.2f conf=%.2f%s, rule %s, %r",
                            expected_error_rate, confidence, (" [BAD]" if not is_acceptable_recognition else ""), kaldi_rule, parsed_output)
                        if self._saving_adaptation_state and is_acceptable_recognition:  # Don't save adaptation state for bad recognitions
                            self._decoder.save_adaptation_state()
                        if self.audio_store:
                            if kaldi_rule and is_acceptable_recognition:  # Don't store audio/metadata for bad recognitions
                                self.audio_store.finalize(parsed_output,
                                    kaldi_rule.parent_grammar.name, kaldi_rule.parent_rule.name,
                                    likelihood=expected_error_rate, has_dictation=kaldi_rule.has_dictation)
                            else:
                                self.audio_store.cancel()

                    self._in_phrase = False
                    self._ignore_current_phrase = False
                    in_complex = False
                    timed_out = False
                    if single:
                        break
                    self.prepare_for_recognition()  # Do any of this leftover, now that phrase is done

                self.call_timer_callback()

        except StopIteration:
            if audio_iter == self._audio_iter:
                self._log.warning("audio iterator stopped unexpectedly")

        finally:
            self._doing_recognition = False
            if (audio_iter == self._audio_iter) and self._audio:
                try:
                    self._audio.stop()  # We started the audio above, so we should stop it
                except Exception:
                    self._log.exception("Error stopping audio")
            if self._deferred_disconnect:
                self.disconnect()

        return not timed_out

    in_phrase = property(lambda self: self._in_phrase,
        doc="Whether or not the engine is currently in the middle of hearing a phrase from the user.")

    def recognize_wave_file(self, filename, realtime=False, **kwargs):
        """
            Does recognition on given wave file, treating it as a single
            utterance (without VAD), then returns.
        """
        self.do_recognition(audio_iter=WavAudio.read_file(filename, realtime=realtime), **kwargs)

    def recognize_wave_file_as_stream(self, filename, realtime=False, **kwargs):
        """
            Does recognition on given wave file, treating it as a stream and
            processing it with VAD to break it into multiple utterances (as with
            normal microphone audio input), then returns.
        """
        self.do_recognition(audio_iter=WavAudio.read_file_with_vad(filename, realtime=realtime), **kwargs)

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

    def add_word_list_to_user_dictation(self, word_list):
        """ Make UserDictation elements able to recognize each item of given
            list of strings *word_list*. Note: all characters will be converted
            to lowercase, and recognized as such. """
        word_list = [str(word).lower() for word in word_list]
        word_list = [word for word in word_list
            if word not in user_dictation_list]
        # if any((word != word.lower()) for word in word_list):
        #     raise ValueError("Cannot recognize words with uppercase")
        user_dictation_list.extend(word_list)

    def add_word_dict_to_user_dictation(self, word_dict):
        """ Make UserDictation elements able to recognize each item of given
            dict of strings *word_dict*. The key is the "spoken form" (which is
            recognized), and the value is the "written form" (which is returned
            as the text in the UserDictation element). Note: all characters in
            the keys will be converted to lowercase, but the values are returned
            as text verbatim. """
        word_dict = {str(key).lower(): str(value) for key, value in word_dict.items()}
        word_dict = {key: value for key, value in word_dict.items()
            if key not in user_dictation_dictlist.keys()}
        # if any((word != word.lower()) for word in word_dict.keys()):
        #     raise ValueError("Cannot recognize words with uppercase")
        user_dictation_dictlist.update(word_dict)

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
        window_info = {}
        if phrase_start:
            fg_window = Window.get_foreground()
            window_info = {
                "executable": fg_window.executable,
                "title": fg_window.title,
                "handle": fg_window.handle,
            }
            for grammar_wrapper in self._iter_all_grammar_wrappers_dynamically():
                grammar_wrapper.phrase_start_callback(**window_info)
        self.prepare_for_recognition()
        self._active_kaldi_rules = set()
        self._kaldi_rules_activity = [False] * self._compiler.num_kaldi_rules
        for grammar_wrapper in self._iter_all_grammar_wrappers_dynamically():
            if grammar_wrapper.active and (not self._any_exclusive_grammars or grammar_wrapper.exclusive):
                for kaldi_rule in grammar_wrapper.kaldi_rule_by_rule_dict.values():
                    if kaldi_rule.active:
                        self._active_kaldi_rules.add(kaldi_rule)
                        self._kaldi_rules_activity[kaldi_rule.id] = True
        self._log.debug("active kaldi_rules (from window %s): %s", window_info, [kr.name for kr in self._active_kaldi_rules])
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
                    return Recognition.construct_empty(self)

                if len(results) > 1:
                    self._log.warning("ambiguity in recognition: %r" % output)
                    # FIXME: improve sorting criterion
                    results.sort(key=lambda result: 100 if result[0].has_dictation else 0)

                kaldi_rule, words = results[0]
                # FIXME: hack, but seems to work fine? only a problem for ambiguous rules containing dictation, which should be handled above
                words_are_dictation_mask = [True] * len(words)

        elif self._compiler.parsing_framework == 'token':
            kaldi_rule, words, words_are_dictation_mask = self._compiler.parse_output(output,
                dictation_info_func=lambda: (self.audio_store.current_audio_data, self._decoder.get_word_align(output)))
            if kaldi_rule is None:
                if words:
                    # We should never receive an unparsable recognition from kaldi, unless it's empty (from noise)
                    self._log.error("unable to parse recognition: %r" % output)
                return Recognition.construct_empty(self)

            if self._log.isEnabledFor(12):
                try:
                    self._log.log(12, "Alignment (word,time,length): %s", self._decoder.get_word_align(output))
                except KaldiError as e:
                    self._log.warning("Exception logging word alignment")

        else:
            raise EngineError("Invalid _compiler.parsing_framework")

        if not words:
            # Empty recognition, so bail before calling into dragonfly parsing/processing
            return Recognition.construct_empty(self)

        return Recognition(self, kaldi_rule=kaldi_rule, words=words, words_are_dictation_mask=words_are_dictation_mask)


#===========================================================================

class Recognition(object):
    """
    Kaldi recognition results class.
    """

    def __init__(self, engine, kaldi_rule, words, words_are_dictation_mask=None):
        assert isinstance(engine, KaldiEngine)
        self.engine = engine
        self.kaldi_rule = kaldi_rule
        self.words = tuple(words)
        if words_are_dictation_mask is None:
            assert not words
            words_are_dictation_mask = ()
        self.words_are_dictation_mask = tuple(words_are_dictation_mask)

        assert ((self.kaldi_rule and self.words and self.words_are_dictation_mask)
            or (not self.kaldi_rule and not self.words and not self.words_are_dictation_mask))
        self.parsed_output = ' '.join(words)
        self.has_dictation = any(words_are_dictation_mask)
        self.expected_error_rate = nan
        self.confidence = nan
        self.acceptable = None
        self.finalized = False

    @classmethod
    def construct_empty(cls, engine):
        return cls(engine, kaldi_rule=None, words=())

    # def __del__(self):
    #     # Exactly one of process() or fail() should be called by someone!
    #     if not self.finalized:
    #         self.engine._log.warning("%s not finalized!", self)
    #     # Note: this can be generated spurriously upon exit or testing

    def process(self, expected_error_rate=None, confidence=None, mimic=False):
        if expected_error_rate is not None: self.expected_error_rate = expected_error_rate
        if confidence is not None: self.confidence = confidence
        self.mimic = mimic
        self.acceptable = True
        assert self.words
        grammar_wrappers = self.engine._grammar_wrappers if mimic else self.engine._grammar_wrappers_copy
        grammar_wrapper = grammar_wrappers[id(self.kaldi_rule.parent_grammar)]
        with debug_timer(self.engine._log.debug, "dragonfly parse time"):
            grammar_wrapper.recognition_callback(self)
        self.finalized = True

    def fail(self, expected_error_rate=None, confidence=None, mimic=False):
        if expected_error_rate is not None: self.expected_error_rate = expected_error_rate
        if confidence is not None: self.confidence = confidence
        self.mimic = mimic
        self.acceptable = False
        self.engine._recognition_observer_manager.notify_failure(results=self)
        self.finalized = True


#===========================================================================

class GrammarWrapper(GrammarWrapperBase):

    def __init__(self, grammar, kaldi_rule_by_rule_dict, engine,
                 recobs_manager):
        GrammarWrapperBase.__init__(self, grammar, engine, recobs_manager)
        self.kaldi_rule_by_rule_dict = kaldi_rule_by_rule_dict

        self.active = True
        self.exclusive = False

    def phrase_start_callback(self, executable, title, handle):
        self.grammar.process_begin(executable, title, handle)

    def recognition_callback(self, recognition):
        words = recognition.words
        rule = recognition.kaldi_rule.parent_rule
        words_are_dictation_mask = recognition.words_are_dictation_mask
        try:
            assert (rule.active and rule.exported), "Kaldi engine should only ever return the correct rule"

            # Prepare the words and rule names for the element parsers
            rule_names = (rule.name,) + (('dgndictation',) if any(words_are_dictation_mask) else ())
            words_rules = tuple((word, 0 if not is_dictation else 1)
                for (word, is_dictation) in zip(words, words_are_dictation_mask))

            # Attempt to parse the recognition
            func = getattr(self.grammar, "process_recognition", None)
            if func:
                if not self._process_grammar_callback(func, words=words,
                                                      results=recognition):
                    # Return early if the method didn't return True or equiv.
                    return

            state = State(words_rules, rule_names, self.engine)
            state.initialize_decoding()
            for result in rule.decode(state):
                if state.finished():
                    root = state.build_parse_tree()
                    notify_args = (words, rule, root, recognition)
                    self.recobs_manager.notify_recognition(*notify_args)
                    with debug_timer(self.engine._log.debug, "rule execution time"):
                        rule.process_recognition(root)
                    self.recobs_manager.notify_post_recognition(*notify_args)
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
