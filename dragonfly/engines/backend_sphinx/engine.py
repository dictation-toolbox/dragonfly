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
Engine class for CMU Pocket Sphinx
"""
from dragonfly.engines.backend_sphinx import is_engine_available
from ..base import EngineBase, EngineError, MimicFailure
from .dictation import SphinxDictationContainer
from .recobs import SphinxRecObsManager
from .compiler import SphinxCompiler
import dragonfly.grammar.state as state_


class SphinxEngine(EngineBase):
    """Speech recognition engine back-end for CMU Pocket Sphinx."""

    _name = "sphinx"
    DictationContainer = SphinxDictationContainer

    def __init__(self):
        EngineBase.__init__(self)

        try:
            import pocketsphinx
            self.sphinx = pocketsphinx
        except ImportError:
            self._log.error("%s: failed to import pocketsphinx module." % self)
            raise EngineError("Failed to import the pocketsphinx module.")

        self._grammar_count = 0
        self._recognition_observer_manager = SphinxRecObsManager(self)

    def connect(self):
        """ Connect to Sphinx somehow. """
        self.sphinx.Pocketsphinx()
        pass  # TODO

    def disconnect(self):
        """ Disconnect from Sphinx somehow. """
        pass  # TODO

    # -----------------------------------------------------------------------
    # Methods for working with grammars.

    def _build_grammar_wrapper(self, grammar):
        super(SphinxEngine, self)._build_grammar_wrapper(grammar)

    def _load_grammar(self, grammar):
        """ Load the given *grammar* and return a wrapper. """
        self._log.debug("Engine %s: loading grammar %s."
                        % (self, grammar.name))

        grammar.engine = self
        wrapper = GrammarWrapper(grammar, self)

        # Dependency checking.
        memo = []
        for r in grammar._rules:
            for d in r.dependencies(memo):
                grammar.add_dependency(d)

        c = SphinxCompiler()
        (compiled_grammar, rule_names) = c.compile_grammar(grammar)
        grammar._rule_names = rule_names

        if is_engine_available():
            self.connect()
            try:
                # TODO Load grammar into/for Sphinx (somehow)
                pass
            except Exception, e:
                self._log.exception("Failed to load grammar %s: %s."
                                    % (grammar, e))
                raise EngineError("Failed to load grammar %s: %s."
                                  % (grammar, e))

        return wrapper

    def _unload_grammar(self, grammar, wrapper):
        """ Unload the given *grammar*. """
        try:
            # Looks like this would cause endless recursion
            # grammar.unload()
            pass
        except Exception, e:
            self._log.exception("Failed to unload grammar %s: %s."
                                % (grammar, e))

    def set_exclusiveness(self, grammar, exclusive):
        try:
            pass
        except Exception, e:
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
        # grammar_object = wrapper.grammar_object
        # grammar_object.activate(rule.name, 0)

    def deactivate_rule(self, rule, grammar):
        self._log.debug("Deactivating rule %s in grammar %s." % (rule.name, grammar.name))
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return
        # grammar_object = wrapper.grammar_object
        # grammar_object.deactivate(rule.name)

    def update_list(self, lst, grammar):
        wrapper = self._get_grammar_wrapper(grammar)
        if not wrapper:
            return
        # grammar_object = wrapper.grammar_object

        # First empty then populate the list.  Use the local variables
        #  n and f as an optimization.
        # n = lst.name
        # f = grammar_object.appendList
        # grammar_object.emptyList(n)
        # [f(n, word) for word in lst.get_list_items()]

    # -----------------------------------------------------------------------
    # Miscellaneous methods.

    def mimic(self, words):
        """ Mimic a recognition of the given *words*. """
        try:
            prepared_words = []
            for word in words:
                if isinstance(word, unicode):
                    word = word.encode()
                prepared_words.append(word)
        except Exception, e:
            raise MimicFailure("Invalid mimic input %r: %s."
                               % (words, e))
        try:
            # TODO Implement or find some way of mimicking words with Sphinx
            # TODO Pass in words as a list to a function:
            # recognitionMimic(prepared_words)
            # TODO Have the function throw a MimicFailure Engine Error if
            # there isn't a matching rule for the words.
            # Wouldn't that just mean that it's just dictation though??
            pass
        except MimicFailure:
            raise MimicFailure("No matching rule found for words %r."
                               % (prepared_words,))

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        # TODO Implement simple config allowing for choice of text-to-speech engine
        # Jasper project has such an implementation:
        # https://github.com/jasperproject/jasper-client
        pass

    def _get_language(self):
        # TODO Write a file with the locale information like this if necessary
        return "en"


class GrammarWrapper(object):

    def __init__(self, grammar, engine):
        self.grammar = grammar
        self.engine = engine

    def begin_callback(self, module_info):
        executable, title, handle = module_info
        self.grammar.process_begin(executable, title, handle)

    def results_callback(self, words, results):
        SphinxEngine._log.debug("Grammar %s: received recognition %r." % (self.grammar._name, words))

        if words == "other":
            func = getattr(self.grammar, "process_recognition_other", None)
            if func:
                words = tuple(unicode(w) for w in results.getWords(0))
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
        words_rules = tuple((unicode(w), r) for w, r in words)
        words = tuple(w for w, r in words_rules)

        # Call the grammar's general process_recognition method, if present.
        func = getattr(self.grammar, "process_recognition", None)
        if func:
            if not func(words):
                return

        # Iterates through this grammar's rules, attempting
        #  to decode each.  If successful, call that rule's
        #  method for processing the recognition and return.

        # TODO Look into how Jasper does this with modules.
        # We probably want to do the same.
        s = state_.State(words_rules, self.grammar._rule_names, self.engine)
        for r in self.grammar._rules:
            if not r.active:
                continue
            s.initialize_decoding()

            # Iterate each result from decoding state 's' with grammar rule 'r'
            for _ in r.decode(s):
                if s.finished():
                    root = s.build_parse_tree()
                    r.process_recognition(root)
                    return

        SphinxEngine._log.warning("Grammar %s: failed to decode recognition %r." % (self.grammar._name, words))
