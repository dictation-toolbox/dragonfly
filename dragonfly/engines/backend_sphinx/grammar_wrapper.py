"""
GrammarWrapper class for CMU Pocket Sphinx engine
"""

import sys

import dragonfly.grammar.state as state_
from dragonfly import Grammar, Window


class GrammarWrapper(object):
    def __init__(self, grammar, engine):
        """
        :type grammar: Grammar
        :type engine: SphinxEngine
        """
        self.grammar = grammar
        self.engine = engine
        self._jsgf_grammar = engine.compiler.compile_grammar(grammar)

    @property
    def jsgf_grammar(self):
        return self._jsgf_grammar

    def process_begin(self):
        """
        Start the dragonfly grammar processing.
        """
        # Get context info for the process_begin method. Dragonfly has a handy
        # static method for this:
        fg_window = Window.get_foreground()
        if sys.platform.startswith("win"):
            process_method = self.grammar.process_begin
        else:
            # Note: get_foreground() is mocked for non-Windows platforms
            # TODO Change to process_begin once cross platform contexts are working
            process_method = self.grammar._process_begin

        # Call the process begin method
        process_method(fg_window.executable, fg_window.title, fg_window.handle)

    def process_results(self, words):
        """
        Start the dragonfly processing of the speech hypothesis.
        :param words: a sequence of (word, rule_id) 2-tuples (pairs)
        """
        self.engine._log.debug("Grammar %s: received recognition %r."
                               % (self.grammar.name, words))

        words_rules = tuple((unicode(w), r) for w, r in words)
        rule_ids = tuple(r for _, r in words_rules)
        words = tuple(w for w, r in words_rules)

        # Call the grammar's general process_recognition method, if present.
        func = getattr(self.grammar, "process_recognition", None)
        if func:
            if not func(words):
                return

        # Iterates through this grammar's rules, attempting to decode each.
        # If successful, call that rule's method for processing the recognition
        # and return.
        s = state_.State(words_rules, rule_ids, self.engine)
        for r in self.grammar.rules:
            # TODO Remove the if windows condition when contexts are working
            if not r.active and sys.platform.startswith("win"):
                continue
            s.initialize_decoding()

            # Iterate each result from decoding state 's' with grammar rule 'r'
            for _ in r.decode(s):
                if s.finished():
                    root = s.build_parse_tree()
                    r.process_recognition(root)
                    return

        self.engine._log.warning("Grammar %s: failed to decode recognition %r."
                                 % (self.grammar.name, words))
