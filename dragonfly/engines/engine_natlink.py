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
    This file implements the Natlink engine class.
"""


#---------------------------------------------------------------------------

natlink = None
from dragonfly.engines.engine_base       import EngineBase


#---------------------------------------------------------------------------

class NatlinkEngine(EngineBase):

    @classmethod
    def is_available(cls):
        try:
            import natlink
        except ImportError:
            return False
        return True


    #-----------------------------------------------------------------------

    def __init__(self):
        global natlink
        if not natlink:
            try:
                import natlink
            except ImportError:
                self._log.error("%s: failed to import natlink module." % self)
                raise EngineError("Failed to import the Natlink module.")



    #-----------------------------------------------------------------------
    # Methods for working with grammars.

    def load_grammar(self, grammar):
        self._log.debug("Engine %s: loading grammar %s."
                        % (self, grammar.name))

        grammar.engine = self
        grammar_object = natlink.GramObj()
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
        all_results = False
        hypothesis = False

        try:
            grammar_object.load(compiled_grammar, all_results, hypothesis)
        except natlink.NatError, e:
            self._log.warning("Engine %s: failed to load: %s." % (self, e))
            return

        self._set_grammar_wrapper(grammar, wrapper)

    def unload_grammar(self, grammar):
        """Unload this grammar from natlink."""
        try:
            grammar_object = self._get_grammar_wrapper(grammar).grammar_object
            grammar_object.setBeginCallback(None)
            grammar_object.setResultsCallback(None)
            grammar_object.setHypothesisCallback(None)
            grammar_object.unload()
        except natlink.NatError, e:
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
        grammar_object = self._get_grammar_wrapper(grammar).grammar_object
        grammar_object.activate(rule.name, 0)

    def deactivate_rule(self, rule, grammar):
        self._log.debug("Deactivating rule %s in grammar %s." % (rule.name, grammar.name))
        grammar_object = self._get_grammar_wrapper(grammar).grammar_object
        grammar_object.deactivate(rule.name)

    def update_list(self, lst, grammar):
        try:
            grammar_object = self._get_grammar_wrapper(grammar).grammar_object
        except AttributeError:
            return

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
    # Methods for handling dictation elements.

    def format_dictation_node(self, node):
        words = node.words()
        formatter = wordinfo.FormatState()
        formatted = formatter.format_words(words)
        self._log.error("formatting: %r - %r" % (words, formatted))
        return formatted


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
