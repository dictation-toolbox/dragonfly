

import logging

from jsgf import Literal, filter_expansion

import dragonfly.grammar.state as state_


class GrammarWrapper(object):
    """
    GrammarWrapper class for CMU Pocket Sphinx engine
    """

    _log = logging.getLogger("engine")

    def __init__(self, grammar, engine, observer_manager, search_name):
        """
        :type grammar: Grammar
        :type engine: SphinxEngine
        """
        self.grammar = grammar
        self.engine = engine
        self._observer_manager = observer_manager
        self.set_search = True
        self._search_name = search_name
        self.exclusive = False

        # Compile the grammar into a JSGF grammar and set the language.
        self._jsgf_grammar = engine.compiler.compile_grammar(grammar)
        self._jsgf_grammar.language_name = engine.language

    def _get_reference_name(self, name):
        return self.engine.compiler.get_reference_name(name)

    def enable_rule(self, name):
        ref_name = self._get_reference_name(name)
        jsgf_rule = self._jsgf_grammar.get_rule_from_name(ref_name)

        # Only enable the rule and set the flag if the rule is disabled.
        if not jsgf_rule.active:
            jsgf_rule.enable()
            self.set_search = True

    def disable_rule(self, name):
        ref_name = self._get_reference_name(name)
        jsgf_rule = self._jsgf_grammar.get_rule_from_name(ref_name)

        # Only disable the rule and set the flag if the rule is enabled.
        if jsgf_rule.active:
            jsgf_rule.disable()
            self.set_search = True

    def update_list(self, lst):
        # Recompile the list again.
        grammar = self._jsgf_grammar
        name = self._get_reference_name(lst.name)
        old_rule = grammar.get_rule_from_name(name)
        new_rule, unknown_words = self.engine.compiler.recompile_list(
            lst, grammar
        )

        # Only replace the old rule if the list has changed.
        if old_rule != new_rule:
            grammar.remove_rule(old_rule, ignore_dependent=True)
            grammar.add_rule(new_rule)
            self.set_search = True

            # Log a warning about unknown words if necessary.
            if unknown_words:
                logger = logging.getLogger("engine.compiler")
                logger.warning("List '%s' used words not found in the "
                               "pronunciation dictionary: %s", name,
                               ", ".join(sorted(unknown_words)))

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
        return self._search_name

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
            if not (r.active and r.exported):
                continue
            s.initialize_decoding()
            for _ in r.decode(s):
                if s.finished():
                    # Build the parse tree used to process this rule.
                    root = s.build_parse_tree()

                    # Notify observers using the manager *before* processing.
                    self._observer_manager.notify_recognition(
                        tuple([word for word, _ in words]),
                        r,
                        root
                    )

                    # Process the rule if not in training mode.
                    if not self.engine.training_session_active:
                        try:
                            r.process_recognition(root)
                            self._observer_manager.notify_post_recognition(
                                tuple([word for word, _ in words]),
                                r,
                                root
                            )
                        except Exception as e:
                            self._log.exception("Failed to process rule "
                                                "'%s': %s" % (r.name, e))
                    return True

        self._log.debug("Grammar %s: failed to decode recognition %r."
                        % (self.grammar.name, words))
        return False
