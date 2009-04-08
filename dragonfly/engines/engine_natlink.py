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
Natlink and DNS engine class
============================================================================

"""

natlink = None
import win32com.client

from .engine_base        import EngineBase
from .dictation_natlink  import NatlinkDictationContainer
from .recobs_natlink     import NatlinkRecObsManager


#---------------------------------------------------------------------------

class NatlinkEngine(EngineBase):
    """ Speech recognition engine back-end for Natlink and DNS. """

    _name = "natlink"
    DictationContainer = NatlinkDictationContainer

    @classmethod
    def is_available(cls):
        """ Check whether Natlink is available. """
        try:
            import natlink
        except ImportError:
            return False

        if natlink.isNatSpeakRunning():
            return True
        else:
            return False


    #-----------------------------------------------------------------------

    def __init__(self):
        global natlink

        EngineBase.__init__(self)

        self._natlink = None
        if natlink:
            self._natlink = natlink
        else:
            try:
                import natlink as natlink_
            except ImportError:
                self._log.error("%s: failed to import natlink module." % self)
                raise EngineError("Failed to import the Natlink module.")
            natlink = natlink_
            self._natlink = natlink_

        self._recognition_observer_manager = NatlinkRecObsManager(self)

    #-----------------------------------------------------------------------
    # Methods for working with grammars.

    def load_grammar(self, grammar):
        """ Load the given *grammar* into natlink. """
        self.load_natlink_grammar(grammar)

    def load_natlink_grammar(self, grammar, all_results=False,
                             hypothesis=False):
        """ Load the given *grammar* into natlink. """
        self._log.debug("Engine %s: loading grammar %s."
                        % (self, grammar.name))

        grammar.engine = self
        grammar_object = self._natlink.GramObj()
        wrapper = GrammarWrapper(grammar, grammar_object, self)

        grammar_object.setBeginCallback(wrapper.begin_callback)
        grammar_object.setResultsCallback(wrapper.results_callback)
        grammar_object.setHypothesisCallback(None)

        # Dependency checking.
        for r in grammar._rules:
            for d in r.dependencies():
                grammar.add_dependency(d)

        c = NatlinkCompiler()
        (compiled_grammar, rule_names) = c.compile_grammar(grammar)
        grammar._rule_names = rule_names

        try:
            grammar_object.load(compiled_grammar, all_results, hypothesis)
        except self._natlink.NatError, e:
            self._log.warning("%s: failed to load grammar %r: %s."
                              % (self, grammar.name, e))
            self._set_grammar_wrapper(grammar, None)
            return

        self._set_grammar_wrapper(grammar, wrapper)

    def unload_grammar(self, grammar):
        """ Unload the given *grammar* from natlink. """
        try:
            grammar_object = self._get_grammar_wrapper(grammar).grammar_object
            grammar_object.setBeginCallback(None)
            grammar_object.setResultsCallback(None)
            grammar_object.setHypothesisCallback(None)
            grammar_object.unload()
        except self._natlink.NatError, e:
            self._log.warning("Engine %s: failed to unload: %s."
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

    def _set_grammar_wrapper(self, grammar, grammar_wrapper):
        grammar._grammar_wrapper = grammar_wrapper

    def _get_grammar_wrapper(self, grammar):
        return grammar._grammar_wrapper


    #-----------------------------------------------------------------------
    # Miscellaneous methods.

    def mimic(self, words):
        """ Mimic a recognition of the given *words*. """
        self._natlink.recognitionMimic(list(words))

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        self._natlink.execScript('TTSPlayString "%s"' % text)

    def _get_language(self):
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
        if words == "other":    words_rules = results.getResults(0)
        elif words == "reject": words_rules = []
        else:                   words_rules = words
        NatlinkEngine._log.debug("Grammar %s: received recognition %r."
                                 % (self.grammar._name, words))

        if hasattr(self.grammar, "process_results"):
            if not self.grammar.process_results(words, results):
                return

        # Iterates through this grammar's rules, attempting
        #  to decode each.  If successful, called that rule's
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


#---------------------------------------------------------------------------

from dragonfly.engines.compiler_natlink  import NatlinkCompiler
import dragonfly.grammar.state as state_
import dragonfly.grammar.wordinfo as wordinfo
