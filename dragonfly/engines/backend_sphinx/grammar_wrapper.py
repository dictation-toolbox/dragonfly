

import logging

from jsgf import Literal, filter_expansion

import dragonfly.grammar.state as state_


class GrammarWrapper(object):
    """
    GrammarWrapper class for CMU Pocket Sphinx engine
    """

    _log = logging.getLogger("engine")

    def __init__(self, grammar, engine, observer_manager):
        """
        :type grammar: Grammar
        :type engine: SphinxEngine
        """
        self.grammar = grammar
        self.engine = engine
        self._observer_manager = observer_manager

        # Compile the grammar into a JSGF grammar and set the language.
        self._jsgf_grammar = engine.compiler.compile_grammar(grammar)
        self._jsgf_grammar.language_name = engine.language

    def _get_reference_name(self, name):
        return self.engine.compiler.get_reference_name(name)

    def enable_rule(self, name):
        self._jsgf_grammar.enable_rule(self._get_reference_name(name))

    def disable_rule(self, name):
        self._jsgf_grammar.disable_rule(self._get_reference_name(name))

    def update_list(self, lst):
        # Remove the old list, recompile the list again and add it to the
        # grammar.
        name = self._get_reference_name(lst.name)
        self._jsgf_grammar.remove_rule(name, ignore_dependent=True)
        new_rule = self.engine.compiler.compile_list(lst)
        self._jsgf_grammar.add_rule(new_rule)

    def compile_jsgf(self):
        return self._jsgf_grammar.compile_as_root_grammar()

    @property
    def grammar_words(self):
        """
        Set of all words used in this grammar.

        :returns: set
        """
        words = []
        for rule in self._jsgf_grammar.rules:
            rule_literals = filter_expansion(
                rule.expansion, lambda x: isinstance(x, Literal) and x.text,
                shallow=True
            )
            for literal in rule_literals:
                words.extend(literal.text.split())

        # Return a set of words with no duplicates.
        return set(words)

    @property
    def search_name(self):
        """
        The name of the Pocket Sphinx search that the engine should use to
        process speech for the grammar.

        :return: str
        """
        return "g_%s" % self._jsgf_grammar.name

    @property
    def grammar_active(self):
        """
        Whether the grammar is enabled and has any active rules.
        :rtype: bool
        """
        return self.grammar.enabled and any(self.grammar.active_rules)

    def process_begin(self, fg_window):
        self.grammar.process_begin(fg_window.executable, fg_window.title,
                                   fg_window.handle)

    def process_words(self, words):
        # Return early if the grammar is disabled or if there are no active
        # rules.
        if not (self.grammar.enabled and self.grammar.active_rules):
            return

        self._log.debug("Grammar %s: received recognition %r."
                        % (self.grammar.name, words))
        if words == "other":
            func = getattr(self.grammar, "process_recognition_other", None)
            if func:
                func(words)
            return
        elif words == "reject":
            func = getattr(self.grammar, "process_recognition_failure", None)
            if func:
                func()
            return

        # If the words argument was not "other" or "reject", then it is a
        # sequence of (word, rule_id) 2-tuples.
        # Call the grammar's general process_recognition method, if present.
        func = getattr(self.grammar, "process_recognition", None)
        if func:
            if not func(words):
                return

        # Iterate through this grammar's rules, attempting to decode each.
        # If successful, call that rule's method for processing the
        # recognition and return.
        s = state_.State(words, self.grammar.rule_names, self.engine)
        for r in self.grammar.rules:
            if not r.active:
                continue
            s.initialize_decoding()
            for _ in r.decode(s):
                if s.finished():
                    # Notify observers using the manager *before* processing.
                    self._observer_manager.notify_recognition(
                        tuple([word for word, _ in words])
                    )

                    # Process the rule if not in training mode.
                    root = s.build_parse_tree()
                    if not self.engine.training_session_active:
                        r.process_recognition(root)

                    return True

        self._log.debug("Grammar %s: failed to decode recognition %r."
                        % (self.grammar.name, words))
        return False
