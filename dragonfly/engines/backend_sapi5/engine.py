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
SAPI 5 engine classes
============================================================================

"""


#---------------------------------------------------------------------------

import logging
import time
import os.path

from datetime import datetime
from ctypes import Structure, c_long, c_int, c_uint, pointer
from six import string_types, integer_types

import pythoncom
import win32con
from win32com.client           import Dispatch, getevents, constants
from win32com.client.gencache  import EnsureDispatch
from ctypes import windll, WinError, WINFUNCTYPE
from ctypes.wintypes import DWORD, HANDLE, HWND, LONG

from ..base                    import (EngineBase, EngineError,
                                       MimicFailure, DelegateTimerManager,
                                       DelegateTimerManagerInterface,
                                       DictationContainerBase,
                                       GrammarWrapperBase)
from .compiler                 import Sapi5Compiler
from .recobs                   import Sapi5RecObsManager
from ...grammar.state          import State
from ...grammar.recobs         import RecognitionObserver
from ...windows.window         import Window


#===========================================================================

class POINT(Structure):
    _fields_ = [('x', c_long),
                ('y', c_long)]

class MSG(Structure):
    _fields_ = [('hwnd', c_int),
                ('message', c_uint),
                ('wParam', c_int),
                ('lParam', c_int),
                ('time', c_int),
                ('pt', POINT)]


class MimicObserver(RecognitionObserver):
    _log = logging.getLogger("SAPI5 RecObs")

    def __init__(self):
        RecognitionObserver.__init__(self)
        self.status = "none"

    def on_recognition(self, words):
        self._log.debug("SAPI5 RecObs on_recognition(): %r" % (words,))
        self.status = "recognition: %r" % (words,)

    def on_failure(self):
        self._log.debug("SAPI5 RecObs on_failure()")
        self.status = "failure"


#===========================================================================

class Sapi5SharedEngine(EngineBase, DelegateTimerManagerInterface):
    """ Speech recognition engine back-end for SAPI 5 shared recognizer. """

    _name = "sapi5shared"
    recognizer_dispatch_name = "SAPI.SpSharedRecognizer"
    DictationContainer = DictationContainerBase

    #-----------------------------------------------------------------------

    def __init__(self, retain_dir=None):
        """
        :param retain_dir: Retains recognized audio and/or  metadata in the
          given directory, saving audio to ``retain_[timestamp].wav`` file
          and metadata to ``retain.tsv``.

          Disabled by default (``None``).
        :type retain_dir: str|None
        """
        EngineBase.__init__(self)
        DelegateTimerManagerInterface.__init__(self)

        EnsureDispatch(self.recognizer_dispatch_name)
        EnsureDispatch("SAPI.SpVoice")
        self._recognizer  = None
        self._speaker     = None
        self._compiler    = None

        self._recognition_observer_manager = Sapi5RecObsManager(self)
        self._timer_manager = DelegateTimerManager(0.02, self)

        if isinstance(retain_dir, string_types) or retain_dir is None:
            self._retain_dir = retain_dir
        else:
            self._retain_dir = None
            self._log.error("Invalid retain_dir: %r" % retain_dir)

    def connect(self):
        """ Connect to back-end SR engine. """
        self._recognizer  = Dispatch(self.recognizer_dispatch_name)
        self._speaker     = Dispatch("SAPI.SpVoice")
        self._compiler    = Sapi5Compiler()

    def disconnect(self):
        """ Disconnect from back-end SR engine. """
        self._recognizer  = None
        self._speaker     = None
        self._compiler    = None

    #-----------------------------------------------------------------------
    # Methods for working with grammars.

    def _load_grammar(self, grammar):
        """ Load the given *grammar*. """
        self._log.debug("Loading grammar %s." % grammar.name)
        if not self._recognizer:
            self.connect()

        # Create recognition context, compile grammar, and create
        #  the grammar wrapper object for managing this grammar.
        context = self._recognizer.CreateRecoContext()
        if self._retain_dir:
            context.RetainedAudio = constants.SRAORetainAudio
        handle = self._compiler.compile_grammar(grammar, context)
        wrapper = GrammarWrapper(grammar, handle, context, self,
                                 self._recognition_observer_manager)

        handle.State = constants.SGSEnabled
        for rule in grammar.rules:
            handle.CmdSetRuleState(rule.name, constants.SGDSActive)
       # self.activate_grammar(grammar)
       # for l in grammar.lists:
       #     l._update()
        handle.CmdSetRuleState("_FakeRule", constants.SGDSActive)

        return wrapper

    def _unload_grammar(self, grammar, wrapper):
        """ Unload the given *grammar*. """
        try:
            wrapper.handle.State = constants.SGSDisabled
        except Exception as e:
            self._log.exception("Failed to unload grammar %s: %s."
                                % (grammar, e))

    def activate_grammar(self, grammar):
        """ Activate the given *grammar*. """
        self._log.debug("Activating grammar %s." % grammar.name)
        grammar_handle = self._get_grammar_wrapper(grammar).handle
        grammar_handle.State = constants.SGSEnabled

    def deactivate_grammar(self, grammar):
        """ Deactivate the given *grammar*. """
        self._log.debug("Deactivating grammar %s." % grammar.name)
        grammar_handle = self._get_grammar_wrapper(grammar).handle
        grammar_handle.State = constants.SGSDisabled

    def activate_rule(self, rule, grammar):
        """ Activate the given *rule*. """
        self._log.debug("Activating rule %s in grammar %s."
                        % (rule.name, grammar.name))
        grammar_handle = self._get_grammar_wrapper(grammar).handle
        grammar_handle.CmdSetRuleState(rule.name, constants.SGDSActive)

    def deactivate_rule(self, rule, grammar):
        """ Deactivate the given *rule*. """
        self._log.debug("Deactivating rule %s in grammar %s."
                        % (rule.name, grammar.name))
        grammar_handle = self._get_grammar_wrapper(grammar).handle
        grammar_handle.CmdSetRuleState(rule.name, constants.SGDSInactive)

    def update_list(self, lst, grammar):
        grammar_handle = self._get_grammar_wrapper(grammar).handle
        list_rule_name = "__list_%s" % lst.name
        rule_handle = grammar_handle.Rules.FindRule(list_rule_name)

        rule_handle.Clear()
        src_state = rule_handle.InitialState
        dst_state = None
        for item in lst.get_list_items():
            src_state.AddWordTransition(dst_state, item)

        grammar_handle.Rules.Commit()

    def set_exclusiveness(self, grammar, exclusive):
        self._log.debug("Setting exclusiveness of grammar %s to %s."
                        % (grammar.name, exclusive))
        wrapper = self._get_grammar_wrapper(grammar)
        if exclusive and wrapper.handle.State != constants.SGSExclusive:
            wrapper.state_before_exclusive = wrapper.handle.State
            wrapper.handle.State = constants.SGSExclusive
        elif not exclusive and wrapper.handle.State == constants.SGSExclusive:
            assert wrapper.state_before_exclusive in (constants.SGSEnabled,
                                                      constants.SGSDisabled)
            wrapper.handle.State = wrapper.state_before_exclusive
        # grammar_handle.SetGrammarState(constants.SPGS_EXCLUSIVE)


    #-----------------------------------------------------------------------
    # Miscellaneous methods.

    def mimic(self, words):
        """
        Mimic a recognition of the given *words*.

        .. note:: This method has a few quirks to be aware of:

           #. Mimic can fail to recognize a command if the relevant grammar
              is not yet active.
           #. Mimic does not work reliably with the shared recognizer unless
              there are one or more exclusive grammars active.
           #. Mimic can **crash the process** in some circumstances, e.g.
              when mimicking non-ASCII characters.

        """
        self._log.debug("SAPI5 mimic: %r" % (words,))
        if isinstance(words, string_types):
            phrase = words
        else:
            phrase = " ".join(words)

        # Fail on empty input.
        if not phrase:
            raise MimicFailure("Invalid mimic input %r" % phrase)

        # Register a recognition observer for checking the success of this
        # mimic.
        observer = MimicObserver()
        observer.register()

        # Emulate recognition of the phrase and wait for recognition to
        # finish, timing out after 2 seconds.
        self._recognizer.EmulateRecognition(phrase)
        timeout = 2
        NULL = c_int(win32con.NULL)
        if timeout != None:
            begin_time = time.time()
            windll.user32.SetTimer(NULL, NULL, int(timeout * 1000), NULL)

        message = MSG()
        message_pointer = pointer(message)
        while (not timeout) or (time.time() - begin_time < timeout):
            if timeout:
                self._log.debug("SAPI5 message loop: %s sec left"
                                % (timeout + begin_time - time.time()))
            else:
                self._log.debug("SAPI5 message loop: no timeout")

            if windll.user32.GetMessageW(message_pointer, NULL, 0, 0) == 0:
                msg = str(WinError())
                self._log.error("GetMessageW() failed: %s" % msg)
                raise EngineError("GetMessageW() failed: %s" % msg)

            self._log.debug("SAPI5 message: %r" % (message.message,))
            if message.message == win32con.WM_TIMER:
                # A timer message means this loop has timed out.
                self._log.debug("SAPI5 message loop timed out: %s sec left"
                                % (timeout + begin_time - time.time()))
                break
            else:
                # Process other messages as normal.
                self._log.debug("SAPI5 message translating and dispatching.")
                windll.user32.TranslateMessage(message_pointer)
                windll.user32.DispatchMessageW(message_pointer)

            if observer.status.startswith("recognition:"):
                # The previous message was a recognition which matched.
                self._log.debug("SAPI5 message caused recognition.")

        # Unregister the observer and check its status.
        observer.unregister()
        if observer.status == "failure":
            raise MimicFailure("Mimic failed.")
        elif observer.status == "none":
            raise MimicFailure("Mimic failed, nothing happened.")

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        self._speaker.Speak(text)

    def _get_language(self):
        if not self._recognizer:
            return "en"

        # Get Windows language identifiers for supported languages from the
        # recognizer's current status information.
        languages = self._recognizer.Status.SupportedLanguages

        # Lookup and return the language tag for the first supported
        # language ID.
        if languages:
            return self._get_language_tag(languages[0])
        else:
            return "en"

    def _has_quoted_words_support(self):
        return False

    def _do_recognition(self):
        """
            Recognize speech in a loop.

            This will also call any scheduled timer functions and ensure
            that the correct window context is used.

        """

        # Register for window change events to activate/deactivate grammars
        # and rules on window changes, including window title changes. This
        # is done here because the SAPI5 'OnPhraseStart' grammar callback is
        # called after grammar state changes are allowed.
        WinEventProcType = WINFUNCTYPE(None, HANDLE, DWORD, HWND, LONG,
                                       LONG, DWORD, DWORD)

        self._last_foreground_window = None
        self._last_foreground_window_title = None

        def callback(hWinEventHook, event, hwnd, idObject, idChild,
                     dwEventThread, dwmsEventTime):
            window = Window.get_foreground()
            # Note: hwnd doesn't always match window.handle, even when
            # foreground window changed (and sometimes it didn't change)
            window_changed = (
                window != self._last_foreground_window or
                window == self._last_foreground_window and
                window.title != self._last_foreground_window_title
            )
            if window_changed:
                self.process_grammars_context(window)
                self._last_foreground_window = window
                self._last_foreground_window_title = window.title

        def set_hook(win_event_proc, event_type):
            return windll.user32.SetWinEventHook(
                event_type, event_type, 0, win_event_proc, 0, 0,
                win32con.WINEVENT_OUTOFCONTEXT)

        win_event_proc = WinEventProcType(callback)
        windll.user32.SetWinEventHook.restype = HANDLE

        [set_hook(win_event_proc, et) for et in
         {win32con.EVENT_SYSTEM_FOREGROUND,
          win32con.EVENT_OBJECT_NAMECHANGE, }]

        # Recognize speech, call timer functions and handle window change
        # events in a loop. Stop on disconnect().
        self.speak('beginning loop!')
        while self._recognizer is not None:
            pythoncom.PumpWaitingMessages()
            self.call_timer_callback()
            time.sleep(0.005)

#---------------------------------------------------------------------------
# Make the shared engine available as Sapi5Engine, for backwards
#  compatibility.

Sapi5Engine = Sapi5SharedEngine


#===========================================================================

class Sapi5InProcEngine(Sapi5SharedEngine):
    """
        Speech recognition engine back-end for SAPI 5 in process
        recognizer.

    """

    _name = "sapi5inproc"
    recognizer_dispatch_name = "SAPI.SpInProcRecognizer"

    def connect(self, audio_source=0):
        """
            Connect to the speech recognition backend.

            The audio source to use for speech recognition can be
            specified using the *audio_source* argument. If it is not
            given, it defaults to the first audio source found.

        """

        Sapi5SharedEngine.connect(self)
        self.select_audio_source(audio_source)

    def get_audio_sources(self):
        """
            Get the available audio sources.

            This method returns a list of audio sources, each represented
            by a 3-element tuple: the index, the description, and the COM
            handle for the audio source.

        """

        available_sources = self._recognizer.GetAudioInputs()
        audio_sources_list = []
        for index, item in enumerate(collection_iter(available_sources)):
            audio_sources_list.append((index, item.GetDescription(), item))
        return audio_sources_list

    def select_audio_source(self, audio_source):
        """
            Configure the speech recognition engine to use the given
            audio source.

            The audio source may be specified as follows:
             - As an *int* specifying the index of the audio source to use
             - As a *str* containing the description of the audio source
               to use, or a substring thereof

            The :meth:`get_audio_sources()` method can be used to
            retrieve the available sources together with their indices
            and descriptions.

        """

        available_sources = self._recognizer.GetAudioInputs()

        if isinstance(audio_source, integer_types):
            # Parameter is the index of the source to use.
            if 0 <= audio_source < available_sources.Count:
                selected_source = available_sources.Item(audio_source)
            else:
                raise EngineError("Invalid audio source index: %r"
                                  " (%s sources available, so index must be"
                                  " in range 0 to %s)"
                                  % (audio_source, available_sources.Count,
                                     available_sources.Count - 1))

        elif isinstance(audio_source, string_types):
            for item in collection_iter(available_sources):
                if audio_source in item.GetDescription():
                    selected_source = item
                    break
            else:
                raise EngineError("Audio source not found: %r"
                                  % (audio_source))

        else:
            raise EngineError("Invalid audio source qualifier: %r"
                              % (audio_source))

        self._log.info("Selecting audio source: %r"
                       % (selected_source.GetDescription(),))
        self._recognizer.AudioInput = selected_source


#---------------------------------------------------------------------------
# Utility generator function for iterating over COM collections.

def collection_iter(collection):
    if not collection:
        return
    for index in range(0, collection.Count):
        yield collection.Item(index)


#---------------------------------------------------------------------------

class GrammarWrapper(GrammarWrapperBase):

    def __init__(self, grammar, handle, context, engine, recobs_manager):
        GrammarWrapperBase.__init__(self, grammar, engine, recobs_manager)
        self.handle = handle
        self.context = context
        self.state_before_exclusive = handle.State

        # Register callback functions which will handle recognizer events.
        base = getevents("SAPI.SpSharedRecoContext")
        class ContextEvents(base): pass
        c = ContextEvents(context)
        c.OnPhraseStart = self.phrase_start_callback
        c.OnRecognition = self.recognition_callback
        if hasattr(grammar, "process_recognition_other"):
            c.OnRecognitionForOtherContext = self.recognition_other_callback
        if hasattr(grammar, "process_recognition_failure"):
            c.OnFalseRecognition = self.recognition_failure_callback

    def phrase_start_callback(self, stream_number, stream_position):
        window = Window.get_foreground()
        self.grammar.process_begin(window.executable, window.title,
                                   window.handle)

    def recognition_callback(self, StreamNumber, StreamPosition,
                             RecognitionType, Result):
        try:
            newResult = Dispatch(Result)
            phrase_info = newResult.PhraseInfo
            rule_name = phrase_info.Rule.Name

            #---------------------------------------------------------------
            # Build a list of rule names for each element.

            # First populate it with the top level rule name.
            element = phrase_info.Rule
            name = element.Name
            start = element.FirstElement
            count = element.NumberOfElements
            rule_names = [name] * count

            # Walk the tree of child rules and put their names in the list.
            stack = [collection_iter(phrase_info.Rule.Children)]
            while stack:
                try: element = next(stack[-1])
                except StopIteration: stack.pop(); continue
                name = element.Name
                start = element.FirstElement
                count = element.NumberOfElements
                rule_names[start:start + count] = [name] * count
                if element.Children:
                    stack.append(collection_iter(element.Children))

            #---------------------------------------------------------------
            # Prepare the words and rule names for the element parsers.

            replacements = [False] * len(rule_names)
            if phrase_info.Replacements:
                for replacement in collection_iter(phrase_info.Replacements):
                    begin = replacement.FirstElement
                    end = begin + replacement.NumberOfElements
                    replacements[begin] = replacement.Text
                    for index in range(begin + 1, end):
                        replacements[index] = True

            results = []
            rule_set = list(set(rule_names))

            elements = phrase_info.Elements
            for index in range(len(rule_names)):
                element = elements.Item(index)
                rule_id = rule_set.index(rule_names[index])

                # Map dictation rule IDs to 1M so that dragonfly recognizes
                # the words as dictation.
                if rule_names[index] == "dgndictation":
                    rule_id = 1000000

                replacement = replacements[index]
                info = [element.LexicalForm, rule_id,
                        element.DisplayText, element.DisplayAttributes,
                        replacement]
                results.append(info)

            #---------------------------------------------------------------
            # Retain audio

            # Only write audio data and metadata if the directory exists.
            retain_dir = self.engine._retain_dir
            if retain_dir and not os.path.isdir(retain_dir):
                self.engine._log.warning(
                    "Audio was not retained because '%s' was not a "
                    "directory" % retain_dir
                )
            elif retain_dir:
                try:
                    file_stream = Dispatch("SAPI.SpFileStream")
                    # Note: application can also retrieve smaller portions
                    # of the audio stream by specifying a starting phrase
                    # element and phrase element length.
                    audio_stream = newResult.Audio()

                    # Make sure we have audio data, which we wouldn't from a
                    # mimic or if the retain flag wasn't set above.
                    if audio_stream:
                        # Write audio data.
                        file_stream.Format = audio_stream.Format
                        now = datetime.now()
                        filename = ("retain_%s.wav"
                                    % now.strftime("%Y-%m-%d_%H-%M-%S_%f"))
                        wav_path = os.path.join(retain_dir, filename)
                        flags = constants.SSFMCreateForWrite
                        file_stream.Open(wav_path, flags)
                        try:
                            file_stream.Write(audio_stream.GetData())
                        finally:
                            file_stream.Close()

                        # Write metadata
                        words = ' '.join([r[2] for r in results])
                        audio_length = int(newResult.Times.Length) / 1e7
                        tsv_path = os.path.join(retain_dir, "retain.tsv")
                        with open(tsv_path, "a") as tsv_file:
                            tsv_file.write('\t'.join([
                                filename, str(audio_length),
                                self.grammar.name, rule_name, words
                            ]) + '\n')
                except:
                    self.engine._log.exception("Exception retaining audio")

            #---------------------------------------------------------------
            # Attempt to parse the recognition.

            func = getattr(self.grammar, "process_recognition", None)
            words = tuple([r[0] for r in results])
            if func:
                if not self._process_grammar_callback(func, words=words,
                                                      results=newResult):
                    return

            s = State(results, rule_set, self.engine)
            for r in self.grammar.rules:
                if not (r.active and r.exported):
                    continue

                s.initialize_decoding()
                for result in r.decode(s):
                    if s.finished():
                        # Notify recognition observers, then process the
                        # rule.
                        root = s.build_parse_tree()
                        notify_args = (words, r, root, newResult)
                        self.recobs_manager.notify_recognition(*notify_args)
                        r.process_recognition(root)
                        self.recobs_manager.notify_post_recognition(
                            *notify_args
                        )
                        return

        except Exception as e:
            Sapi5Engine._log.error("Grammar %s: exception: %s"
                                   % (self.grammar._name, e), exc_info=True)

        #-------------------------------------------------------------------
        # If this point is reached, then the recognition was not
        #  processed successfully..

        self.engine._log.error("Grammar %s: failed to decode"
                               " recognition %r."
                               % (self.grammar._name,
                                  [r[0] for r in results]))

    def recognition_other_callback(self, StreamNumber, StreamPosition):
        # Note that SAPI 5.3 doesn't offer access to the actual
        #  recognition contents during a
        #  OnRecognitionForOtherContext event.
        func = getattr(self.grammar, "process_recognition_other", None)
        self._process_grammar_callback(func, words=False, results=None)

    def recognition_failure_callback(self, StreamNumber, StreamPosition,
                                     Result):
        func = getattr(self.grammar, "process_recognition_failure", None)
        self._process_grammar_callback(func, results=Dispatch(Result))
