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
from win32com.client import constants
from pywintypes import com_error

import dragonfly.grammar.state as state_
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
        context = self._recognizer.CreateRecoContext()
        handle = self._compiler.compile_grammar(grammar, context)
        wrapper = GrammarWrapper(grammar, handle, context, self)
        self._set_grammar_wrapper(grammar, wrapper)

        self.activate_grammar(grammar)
        for l in grammar.lists:
            l._update()
        for r in grammar.rules:
            self.activate_rule(r, grammar)

    def activate_grammar(self, grammar):
        self._log.error("Activating grammar %s." % grammar.name)
        grammar_handle = self._get_grammar_wrapper(grammar).handle
        self._log.error("Grammar state: %s." % grammar_handle.State)
        grammar_handle.State = constants.SGSEnabled
        self._log.error("Grammar state: %s." % grammar_handle.State)
#        grammar_handle.DictationLoad(LoadOption=constants.SLODynamic)
#        grammar_handle.DictationLoad(LoadOption=constants.SLOStatic)
        grammar_handle.DictationSetState(constants.SGDSActive)
#        grammar_handle.DictationSetState(constants.SGDSInactive)

        for rule_handle in collection_iter(grammar_handle.Rules):
            self._log.error("Activating rule: %r." % rule_handle.Name)
            if rule_handle.Name == "dgndictation":
                self._log.error(" Except rule: %r." % rule_handle.Name)
                grammar_handle.CmdSetRuleState(rule_handle.Name, constants.SGDSInactive)
                continue
            grammar_handle.CmdSetRuleState(rule_handle.Name, constants.SGDSActive)

    def activate_rule(self, rule, grammar):
        self._log.error("Activating rule %s in grammar %s." % (rule.name, grammar.name))
        grammar_handle = self._get_grammar_wrapper(grammar).handle
        grammar_handle.Rules.Commit()
        grammar_handle.CmdSetRuleState(rule.name, constants.SGDSActive)
#        grammar_handle.Rules.Commit()
        grammar_handle.Rules.CommitAndSave()

    def update_list(self, lst, grammar):
        grammar_handle = self._get_grammar_wrapper(grammar).handle
        list_rule_name = "__list_%s" % lst.name
        self._log.error("%s: list rule %r." % (self, list_rule_name))
        rule_handle = grammar_handle.Rules.FindRule(list_rule_name)
        self._log.error("%s: rule handle %s." % (self, rule_handle))

        rule_handle.Clear()
        src_state = rule_handle.InitialState
        dst_state = None
        for item in lst.get_list_items():
            self._log.error("%s: adding item %r." % (self, item))
            src_state.AddWordTransition(dst_state, item)

        grammar_handle.Rules.Commit()

    def _set_grammar_wrapper(self, grammar, grammar_wrapper):
        grammar._grammar_wrapper = grammar_wrapper

    def _get_grammar_wrapper(self, grammar):
        return grammar._grammar_wrapper


    #-----------------------------------------------------------------------
    # Methods for handling dictation elements.

    def format_dictation_node(self, node):
        results = node.full_results()
        self._log.error("%s: format the dictation of the %r." % (self, results))
        return " ".join(r[2] for r in results)


    #-----------------------------------------------------------------------
    # Methods for ...

    _speaker = win32com.client.Dispatch("SAPI.SpVoice")
    def speak(self, text):
        self._speaker.Speak(text)


#---------------------------------------------------------------------------
# Utility generator function for iterating over COM collections.

def collection_iter(collection):
    if not collection:
        return
    for index in xrange(0, collection.Count):
        yield collection.Item(index)


#---------------------------------------------------------------------------

class GrammarWrapper(object):

    def __init__(self, grammar, handle, context, engine):
        self.grammar = grammar
        self.handle = handle
        self.engine = engine

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
            phrase_info = newResult.PhraseInfo
            rule_name = phrase_info.Rule.Name

            #---------------------------------------------------------------
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak('you said '+phrase_info.GetText())

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
                try: element = stack[-1].next()
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
                replacement = replacements[index]
                info = [element.LexicalForm, rule_id,
                        element.DisplayText, element.DisplayAttributes,
                        replacement]
                results.append(info)

            #---------------------------------------------------------------

            s = state_.State(results, rule_set, self.engine)
            for r in self.grammar._rules:
                if r.name != rule_name:
                    continue
                s.initialize_decoding()
                for result in r.decode(s):
                    if s.finished():
                        root = s.build_parse_tree()
                        r.process_recognition(root)
                        return

        except Exception, e:
            Sapi5Engine._log.error("Grammar %s: exception: %s"
                                   % (self.grammar._name, e), exc_info=True)

        Sapi5Engine._log.error("Grammar %s: failed to decode"
                                 " recognition %r."
                                 % (self.grammar._name, words))
