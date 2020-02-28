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
SR back-end for DNS and Natlink
============================================================================

Detecting sleep mode
----------------------------------------------------------------------------

 - http://blogs.msdn.com/b/tsfaware/archive/2010/03/22/detecting-sleep-mode-in-sapi.aspx

"""

import os.path
import sys
import pywintypes
from datetime import datetime
from locale import getpreferredencoding
from six import text_type, binary_type, string_types, PY2
from ..base        import EngineBase, EngineError, MimicFailure
from ...error import GrammarError
from .dictation    import NatlinkDictationContainer
from .recobs       import NatlinkRecObsManager
from .timer        import NatlinkTimerManager
from .compiler     import NatlinkCompiler
import dragonfly.grammar.state as state_


# ---------------------------------------------------------------------------

def map_word(word, encoding=getpreferredencoding(do_setlocale=False)):
    """
    Wraps output from Dragon.

    This wrapper ensures text output from the engine is Unicode. It assumes the
    encoding of byte streams is the current locale's preferred encoding by default.
    """
    if isinstance(word, text_type):
        return word
    elif isinstance(word, binary_type):
        return word.decode(encoding)
    return word


class NatlinkEngine(EngineBase):
    """ Speech recognition engine back-end for Natlink and DNS. """

    _name = "natlink"
    DictationContainer = NatlinkDictationContainer

    #-----------------------------------------------------------------------

    def __init__(self, retain_dir=None):
        EngineBase.__init__(self)

        self.natlink = None
        try:
            import natlink
        except ImportError:
            self._log.error("%s: failed to import natlink module." % self)
            raise EngineError("Requested engine 'natlink' is not available: Natlink is not installed.")
        self.natlink = natlink

        self._grammar_count = 0
        self._recognition_observer_manager = NatlinkRecObsManager(self)
        self._timer_manager = NatlinkTimerManager(0.02, self)
        self._retain_dir = None
        try:
            self.set_retain_directory(retain_dir)
        except EngineError as err:
            self._retain_dir = None
            self._log.error(err)

    def connect(self):
        """ Connect to natlink with Python threading support enabled. """
        self.natlink.natConnect(True)

    def disconnect(self):
        """ Disconnect from natlink. """
        # Unload all grammars from the engine so that Dragon doesn't keep
        # recognizing them.
        for grammar in self.grammars:
            grammar.unload()

        # Close the the waitForSpeech() dialog box if it is active.
        from dragonfly import Window
        target_title = "Natlink / Python Subsystem"
        for window in Window.get_matching_windows(title=target_title):
            if window.is_visible:
                try:
                    window.close()
                except pywintypes.error:
                    pass
                break

        # Finally disconnect from natlink.
        self.natlink.natDisconnect()

    # -----------------------------------------------------------------------
    # Methods for working with grammars.

    def _load_grammar(self, grammar):
        """ Load the given *grammar* into natlink. """
        self._log.debug("Engine %s: loading grammar %s."
                        % (self, grammar.name))

        grammar_object = self.natlink.GramObj()
        wrapper = GrammarWrapper(grammar, grammar_object, self,
                                 self._recognition_observer_manager)
        grammar_object.setBeginCallback(wrapper.begin_callback)
        grammar_object.setResultsCallback(wrapper.results_callback)
        grammar_object.setHypothesisCallback(None)

        c = NatlinkCompiler()
        (compiled_grammar, rule_names) = c.compile_grammar(grammar)
        grammar._rule_names = rule_names

        all_results = (hasattr(grammar, "process_recognition_other")
                       or hasattr(grammar, "process_recognition_failure"))
        hypothesis = False

        attempt_connect = False
        try:
            grammar_object.load(compiled_grammar, all_results, hypothesis)
        except self.natlink.NatError as e:
            # If loading failed because we're not connected yet,
            #  attempt to connect to natlink and reload the grammar.
            if (str(e) == "Calling GramObj.load is not allowed before"
                          " calling natConnect"):
                attempt_connect = True
            else:
                self._log.exception("Failed to load grammar %s: %s."
                                    % (grammar, e))
                raise EngineError("Failed to load grammar %s: %s."
                                  % (grammar, e))
        if attempt_connect:
            self.connect()
            try:
                grammar_object.load(compiled_grammar, all_results, hypothesis)
            except self.natlink.NatError as e:
                self._log.exception("Failed to load grammar %s: %s."
                                    % (grammar, e))
                raise EngineError("Failed to load grammar %s: %s."
                                  % (grammar, e))

        return wrapper

    def _unload_grammar(self, grammar, wrapper):
        """ Unload the given *grammar* from natlink. """
        try:
            grammar_object = wrapper.grammar_object
            grammar_object.unload()
            grammar_object.setBeginCallback(None)
            grammar_object.setResultsCallback(None)
            grammar_object.setHypothesisCallback(None)
        except self.natlink.NatError as e:
            self._log.exception("Failed to unload grammar %s: %s."
                                % (grammar, e))

    def set_exclusiveness(self, grammar, exclusive):
        try:
            grammar_object = self._get_grammar_wrapper(grammar).grammar_object
            grammar_object.setExclusive(exclusive)
        except self.natlink.NatError as e:
            self._log.exception("Engine %s: failed set exclusiveness: %s."
                                % (self, e))

    def activate_grammar(self, grammar):
        self._log.debug("Activating grammar %s." % grammar.name)
        pass

    def deactivate_grammar(self, grammar):
        self._log.debug("Deactivating grammar %s." % grammar.name)
        pass

    def activate_rule(self, rule, grammar):
        self._log.debug("Activating rule %s in grammar %s." % (rule.name, grammar.name))
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return
        grammar_object = wrapper.grammar_object
        grammar_object.activate(rule.name, 0)

    def deactivate_rule(self, rule, grammar):
        self._log.debug("Deactivating rule %s in grammar %s." % (rule.name, grammar.name))
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return
        grammar_object = wrapper.grammar_object
        grammar_object.deactivate(rule.name)

    def update_list(self, lst, grammar):
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return
        grammar_object = wrapper.grammar_object

        # First empty then populate the list.  Use the local variables
        #  n and f as an optimization.
        n = lst.name
        f = grammar_object.appendList
        grammar_object.emptyList(n)
        [f(n, word) for word in lst.get_list_items()]


    #-----------------------------------------------------------------------
    # Miscellaneous methods.

    def _do_recognition(self):
        self.natlink.waitForSpeech()

    def mimic(self, words):
        """ Mimic a recognition of the given *words*. """
        if isinstance(words, string_types):
            words = words.split()

        try:
            prepared_words = []
            if PY2:
                encoding = getpreferredencoding()
                for word in words:
                    if isinstance(word, text_type):
                        word = word.encode(encoding)
                    prepared_words.append(word)
            else:
                for word in words:
                    prepared_words.append(word)
            if len(prepared_words) == 0:
                raise TypeError("empty list or string")
        except Exception as e:
            raise MimicFailure("Invalid mimic input %r: %s."
                               % (words, e))
        try:
            self.natlink.recognitionMimic(prepared_words)
        except self.natlink.MimicFailed:
            raise MimicFailure("No matching rule found for words %r."
                               % (prepared_words,))

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        # Store the current mic state.
        mic_state = self.natlink.getMicState()

        # Say the text.
        self.natlink.execScript('TTSPlayString "%s"' % text)

        # Restore the previous mic state if necessary.
        # This is to have consistent behaviour for each version of Dragon.
        if mic_state != self.natlink.getMicState():
            self.natlink.setMicState(mic_state)

    def _get_language(self):
        # Get a Windows language identifier from Dragon.
        import win32com.client
        app = win32com.client.Dispatch("Dragon.DgnEngineControl")
        language = app.SpeakerLanguage("")

        # Lookup the language tags.
        tags = self._language_tags.get(language)
        if tags:
            return tags[0]

        # The _language_tags dictionary didn't contain the language, so
        # get the best match by using the primary language identifier.
        # This allows us to match unlisted language variants.
        primary_id = language & 0x00ff
        for lang_id, (tag, _) in self._language_tags.items():
            if primary_id == lang_id & 0x00ff:  # Match found.
                return tag

        # Speaker language wasn't found.
        self._log.error("Unknown speaker language: 0x%04x" % language)
        raise GrammarError("Unknown speaker language: 0x%04x" % language)

    _language_tags = {
                      0x0c09: ("en", "AustralianEnglish"),
                      0xf00a: ("es", "CastilianSpanish"),
                      0x0413: ("nl", "Dutch"),
                      0x0009: ("en", "English"),
                      0x040c: ("fr", "French"),
                      0x0407: ("de", "German"),
                      0xf009: ("en", "IndianEnglish"),
                      0x0410: ("it", "Italian"),
                      0x0411: ("jp", "Japanese"),
                      0xf40a: ("es", "LatinAmericanSpanish"),
                      0x0416: ("pt", "Portuguese"),
                      0xf409: ("en", "SingaporeanEnglish"),
                      0x040a: ("es", "Spanish"),
                      0x0809: ("en", "UKEnglish"),
                      0x0409: ("en", "USEnglish"),
                      0xf809: ("en", "CAEnglish"),
                     }

    def set_retain_directory(self, retain_dir):
        """
        Set the directory where audio data is saved.

        Retaining audio data may be useful for acoustic model training. This
        is disabled by default.

        If a relative path is used and the code is running via natspeak.exe,
        then the path will be made relative to the Natlink user directory or
        base directory (e.g. ``MacroSystem``).

        :param retain_dir: retain directory path
        :type retain_dir: string|None
        """
        is_string = isinstance(retain_dir, string_types)
        if not (retain_dir is None or is_string):
            raise EngineError("Invalid retain_dir: %r" % retain_dir)

        if is_string:
            # Handle relative paths by using the Natlink user directory or
            # base directory. Only do this if running via natspeak.exe.
            try:
                import natlinkstatus
            except ImportError:
                natlinkstatus = None
            running_via_natspeak = (
                sys.executable.endswith("natspeak.exe") and
                natlinkstatus is not None
            )
            if not os.path.isabs(retain_dir) and running_via_natspeak:
                status = natlinkstatus.NatlinkStatus()
                user_dir = status.getUserDirectory()
                retain_dir = os.path.join(
                    # Use the base dir if user dir isn't set.
                    user_dir if user_dir else status.BaseDirectory,
                    retain_dir
                )

        # Set the retain directory.
        self._retain_dir = retain_dir

#---------------------------------------------------------------------------


class GrammarWrapper(object):

    def __init__(self, grammar, grammar_object, engine, observer_manager):
        self.grammar = grammar
        self.grammar_object = grammar_object
        self.engine = engine
        self.observer_manager = observer_manager

    def begin_callback(self, module_info):
        executable, title, handle = tuple(map_word(word)
                                          for word in module_info)
        self.grammar.process_begin(executable, title, handle)

    def results_callback(self, words, results):
        NatlinkEngine._log.debug("Grammar %s: received recognition %r."
                                 % (self.grammar._name, words))

        if words == "other":
            func = getattr(self.grammar, "process_recognition_other", None)
            if func:
                words = tuple(map_word(w)
                              for w in results.getWords(0))
                func(words)
            return
        elif words == "reject":
            func = getattr(self.grammar, "process_recognition_failure", None)
            if func:
                func()
            return

        # If the words argument was not "other" or "reject", then
        #  it is a sequence of (word, rule_id) 2-tuples.  Convert this
        #  into a tuple of unicode objects.

        words_rules = tuple((map_word(w), r) for w, r in words)
        words = tuple(w for w, r in words_rules)

        # Call the grammar's general process_recognition method, if present.
        func = getattr(self.grammar, "process_recognition", None)
        if func:
            if not func(words):
                return

        # Iterates through this grammar's rules, attempting
        #  to decode each.  If successful, call that rule's
        #  method for processing the recognition and return.
        s = state_.State(words_rules, self.grammar._rule_names, self.engine)
        for r in self.grammar._rules:
            if not (r.active and r.exported): continue
            s.initialize_decoding()
            for result in r.decode(s):
                if s.finished():
                    self._retain_audio(words, results, r.name)
                    root = s.build_parse_tree()

                    # Notify observers using the manager *before*
                    # processing.
                    self.observer_manager.notify_recognition(words, r, root)

                    r.process_recognition(root)

                    # Notify observers using the manager *after*
                    # processing.
                    self.observer_manager.notify_post_recognition(words, r, root)
                    return

        NatlinkEngine._log.warning("Grammar %s: failed to decode"
                                   " recognition %r."
                                   % (self.grammar._name, words))

    def _retain_audio(self, words, results, rule_name):
        # Only write audio data and metadata if the directory exists.
        retain_dir = self.engine._retain_dir
        if retain_dir and not os.path.isdir(retain_dir):
            self.engine._log.warning(
                "Audio was not retained because '%s' was not a "
                "directory" % retain_dir
            )
        elif retain_dir:
            try:
                audio = results.getWave()
                # Make sure we have audio data
                if len(audio) > 0:
                    # Write audio data.
                    now = datetime.now()
                    filename = ("retain_%s.wav"
                                % now.strftime("%Y-%m-%d_%H-%M-%S_%f"))
                    wav_path = os.path.join(retain_dir, filename)
                    with open(wav_path, "wb") as f:
                        f.write(audio)

                    # Write metadata
                    text = ' '.join(words)
                    audio_length = float(len(audio) / 2) / 11025  # assumes 11025Hz 16bit mono
                    tsv_path = os.path.join(retain_dir, "retain.tsv")
                    with open(tsv_path, "a") as tsv_file:
                        tsv_file.write('\t'.join([
                            filename, text_type(audio_length),
                            self.grammar.name, rule_name, text
                        ]) + '\n')
            except:
                self.engine._log.exception("Exception retaining audio")
