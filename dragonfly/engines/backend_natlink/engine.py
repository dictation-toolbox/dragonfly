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
from six import text_type

from ..base        import EngineBase, EngineError, MimicFailure
from ...error import GrammarError
from .dictation    import NatlinkDictationContainer
from .recobs       import NatlinkRecObsManager
from .timer        import NatlinkTimerManager
from .compiler     import NatlinkCompiler
import dragonfly.grammar.state as state_


#---------------------------------------------------------------------------

class NatlinkEngine(EngineBase):
    """ Speech recognition engine back-end for Natlink and DNS. """

    _name = "natlink"
    DictationContainer = NatlinkDictationContainer

    #-----------------------------------------------------------------------

    def __init__(self):
        EngineBase.__init__(self)

        self.natlink = None
        try:
            import natlink
        except ImportError:
            self._log.error("%s: failed to import natlink module." % self)
            raise EngineError("Failed to import the Natlink module.")
        self.natlink = natlink

        self._grammar_count = 0
        self._recognition_observer_manager = NatlinkRecObsManager(self)
        self._timer_manager = NatlinkTimerManager(0.02, self)

    def connect(self):
        """ Connect to natlink with Python threading support enabled. """
        self.natlink.natConnect(True)

    def disconnect(self):
        """ Disconnect from natlink. """
        self.natlink.natDisconnect()

    #-----------------------------------------------------------------------
    # Methods for working with grammars.

    def _load_grammar(self, grammar):
        """ Load the given *grammar* into natlink. """
        self._log.debug("Engine %s: loading grammar %s."
                        % (self, grammar.name))

        grammar.engine = self
        grammar_object = self.natlink.GramObj()
        wrapper = GrammarWrapper(grammar, grammar_object, self)
        grammar_object.setBeginCallback(wrapper.begin_callback)
        grammar_object.setResultsCallback(wrapper.results_callback)
        grammar_object.setHypothesisCallback(None)

        # Dependency checking.
        memo = []
        for r in grammar._rules:
            for d in r.dependencies(memo):
                grammar.add_dependency(d)

        c = NatlinkCompiler()
        (compiled_grammar, rule_names) = c.compile_grammar(grammar)
        grammar._rule_names = rule_names

        if (hasattr(grammar, "process_recognition_other")
            or hasattr(grammar, "process_recognition_failure")):
            all_results = True
        else:
            all_results = False
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

    def mimic(self, words):
        """ Mimic a recognition of the given *words*. """
        try:
            prepared_words = []
            for word in words:
                if isinstance(word, text_type):
                    word = word.encode("windows-1252")
                prepared_words.append(word)
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
        self.natlink.execScript('TTSPlayString "%s"' % text)

        # Turn on the mic if necessary so the user can start speaking again.
        # This is to make the expected behaviour consistent for each version
        # of Dragon.
        if self.natlink.getMicState() != "on":
            self.natlink.setMicState("on")

    def _get_language(self):
        import win32com.client
        app = win32com.client.Dispatch("Dragon.DgnEngineControl")
        language = app.SpeakerLanguage("")
        try:
            tag = self._language_tags[language]
            tag = tag[0]
        except KeyError:
            self._log.error("Unknown speaker language: 0x%04x" % language)
            raise GrammarError("Unknown speaker language: 0x%04x" % language)
        return tag

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
                     }

#---------------------------------------------------------------------------

class GrammarWrapper(object):

    def __init__(self, grammar, grammar_object, engine):
        self.grammar = grammar
        self.grammar_object = grammar_object
        self.engine = engine

    def begin_callback(self, module_info):
        executable, title, handle = module_info
        self.grammar.process_begin(executable, title, handle)

    def results_callback(self, words, results):
        NatlinkEngine._log.debug("Grammar %s: received recognition %r."
                                 % (self.grammar._name, words))

        if words == "other":
            func = getattr(self.grammar, "process_recognition_other", None)
            if func:
                words = tuple(text_type(w).encode("windows-1252")
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
        def map_word(w):
            if isinstance(w, text_type):
                return w
            else:
                return w.decode("windows-1252")

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
            if not r.active: continue
            s.initialize_decoding()
            for result in r.decode(s):
                if s.finished():
                    root = s.build_parse_tree()
                    r.process_recognition(root)
                    return

        NatlinkEngine._log.warning("Grammar %s: failed to decode"
                                   " recognition %r."
                                   % (self.grammar._name, words))
