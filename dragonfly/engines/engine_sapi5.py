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
    This file implements the SAPI 5 engine class.
"""


#---------------------------------------------------------------------------

import win32com.client
from pywintypes import com_error

from dragonfly.engines.engine_base     import EngineBase
from dragonfly.engines.compiler_sapi5  import Sapi5Compiler


#---------------------------------------------------------------------------

class Sapi5Engine(EngineBase):

    @classmethod
    def is_available(cls):
        try:
            win32com.client.Dispatch("SAPI.SpSharedRecognizer")
        except com_error:
            return False
        return True


    #-----------------------------------------------------------------------

    def __init__(self):
        self._recognizer = win32com.client.Dispatch("SAPI.SpSharedRecognizer")
        self._compiler = Sapi5Compiler()


    #-----------------------------------------------------------------------
    # Methods for working with grammars.

    def load_grammar(self, grammar):
        self._log.error("Loading grammar %s." % grammar.name)
        grammar.engine = self
        (context, handle) = self._compiler.compile_grammar(grammar, self._recognizer)
        wrapper = GrammarWrapper(grammar, handle, context)
        self._set_grammar_wrapper(grammar, wrapper)

        self.activate_grammar(grammar)
        for r in grammar.rules:
           self.activate_rule(r, grammar)

    def activate_grammar(self, grammar):
        self._log.error("Activating grammar %s." % grammar.name)
        grammar_handle = self._get_grammar_wrapper(grammar).handle
        grammar_handle.DictationSetState(0)

    def activate_rule(self, rule, grammar):
        self._log.error("Activating rule %s in grammar %s." % (rule.name, grammar.name))
        grammar_handle = self._get_grammar_wrapper(grammar).handle
        grammar_handle.Rules.Commit()
        grammar_handle.CmdSetRuleState(rule.name, 1)
        grammar_handle.Rules.CommitAndSave()

    def _set_grammar_wrapper(self, grammar, grammar_wrapper):
        grammar._grammar_wrapper = grammar_wrapper

    def _get_grammar_wrapper(self, grammar):
        return grammar._grammar_wrapper


#---------------------------------------------------------------------------

class GrammarWrapper(object):

    def __init__(self, grammar, handle, context):
        self.grammar = grammar
        self.handle = handle

        base = win32com.client.getevents("SAPI.SpSharedRecoContext")
        Sapi5Engine._log.error('base %s' % base)
        class ContextEvents(base): pass
        c = ContextEvents(context)
        c.OnRecognition = self.recognition_callback

    def begin_callback(self):
        pass

    def recognition_callback(self, StreamNumber, StreamPosition, RecognitionType, Result):
        try:
            newResult = win32com.client.Dispatch(Result)
            Sapi5Engine._log.error('TEXT: %r' % newResult.PhraseInfo.GetText())

            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            def say(text):
                speaker.Speak(text)

            rule_name = newResult.PhraseInfo.Rule.Name

            say('you said '+newResult.PhraseInfo.GetText())
            for r in self.grammar._rules:
                if r.name != rule_name:
                    continue
                r.process_recognition(None)
        except Exception, e:
            Sapi5Engine._log.warning("Grammar %s: exception: %s"
                                 % (self.grammar._name, e))

        Sapi5Engine._log.warning("Grammar %s: failed to decode"
                                 " recognition %r."
                                 % (self.grammar._name, words))
