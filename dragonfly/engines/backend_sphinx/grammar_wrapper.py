"""
GrammarWrapper class for CMU Pocket Sphinx engine
"""
import functools
from six import text_type

from jsgf import RuleRef, map_expansion, Literal, find_expansion, filter_expansion
from jsgf.ext import SequenceRule, DictationGrammar, only_dictation_in_expansion, \
    dictation_in_expansion

import dragonfly.grammar.state as state_
from dragonfly import Grammar
from dragonfly2jsgf import LinkedRule


@functools.total_ordering
class ProcessingState(object):
    """
    State class used to process matching rules in a GrammarWrapper.

    ProcessingState objects can be compared to find the best state to process.
    """
    def __init__(self, wrapper, speech, use_linked_rules=False):
        """
        :type wrapper: GrammarWrapper
        :type speech: str
        :type use_linked_rules: bool
        """
        self._wrapper = wrapper
        self._post_collection_tasks = []
        self.speech = speech

        # This is used when mimicking speech as words.
        self.use_linked_rules = use_linked_rules
        self.in_progress_rules = []
        self.complete_rules = []
        self.speech_is_dictation = self.wrapper.engine.recognising_dictation

        # Collect matching rules into this state's rule lists.
        self.wrapper.collect_matching_rules(self)

    @property
    def wrapper(self):
        """
        The GrammarWrapper this state object was created for.
        :rtype: GrammarWrapper
        """
        return self._wrapper

    @property
    def is_processable(self):
        """
        Whether this state can be processed by its GrammarWrapper.
        """
        return bool(self.in_progress_rules or self.complete_rules)

    @property
    def complete_sequence_rules(self):
        return [x for x in self.complete_rules if isinstance(x, SequenceRule)]

    @property
    def repeatable_complete_sequence_rules(self):
        return [x for x in self.complete_sequence_rules if x.can_repeat]

    @property
    def complete_normal_rules(self):
        return [x for x in self.complete_rules if not isinstance(x, SequenceRule)]

    @property
    def matched_rules(self):
        return self.in_progress_rules + self.complete_rules

    def process(self, timed_out=False, notify_only=False):
        """
        Process this state object by calling the wrapper's process method.
        """
        self.wrapper.process(self, timed_out, notify_only)

    def add_post_collection_task(self, task):
        """
        Add a post collection task to be executed when `do_post_collection_tasks` is
        called.
        :param task: callable object
        :return:
        """
        if not callable(task):
            raise TypeError("%s is not a callable object" % task)
        self._post_collection_tasks.append(task)

    def do_post_collection_tasks(self):
        # Execute each task in the order they were added.
        while self._post_collection_tasks:
            self._post_collection_tasks.pop(0)()

    def __lt__(self, other):
        return (
            # Favour processable states.
            not self.is_processable and other.is_processable

            # Favour a specific grammar context over no context.
            or not self.wrapper.grammar._context and other.wrapper.grammar._context
        )

    def __eq__(self, other):
        return (self.speech == other.speech and self.wrapper == other.wrapper
                and self.in_progress_rules == other.in_progress_rules
                and self.complete_rules == other.complete_rules)

    def __hash__(self):
        return hash(self.wrapper.grammar.name)


class GrammarWrapper(object):
    def __init__(self, grammar, engine):
        """
        :type grammar: Grammar
        :type engine: SphinxEngine
        """
        self.grammar = grammar
        self.engine = engine

        # Compile the grammar into a JSGF grammar and add those rules into
        # a JSGF DictationGrammar.
        self._jsgf_grammar = engine.compiler.compile_grammar(grammar)
        self._jsgf_grammar.language_name = engine.language
        self._dictation_grammar = DictationGrammar(self._jsgf_grammar.rules)
        self._dictation_grammar.language_name = engine.language

        # Set internal variables
        self._in_progress_sequence_rules = []

        # Set the default search name based on whether only dictation can be matched
        grammar_has_jsgf = False
        for rule in self._dictation_grammar.match_rules:
            if not rule.active:
                continue  # skip disabled rules; they can't be matched
            if not only_dictation_in_expansion(rule.expansion):
                grammar_has_jsgf = True
                break

        if grammar_has_jsgf:
            self._default_search_name = self.grammar.name
        else:
            self._default_search_name = self.engine.dictation_search_name

        # Set the default value of search_name
        self._search_name = self._default_search_name

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
    def dictation_grammar(self):
        return self._dictation_grammar

    @property
    def search_name(self):
        """
        The name of the Pocket Sphinx search that the engine should use to process
        speech for the grammar.
        :return: str
        """
        return self._search_name

    @property
    def default_search_name(self):
        """
        The name of the default Pocket Sphinx search that the engine should use to
        process speech for the grammar.

        This is not necessarily the current search that should be used for the
        grammar.
        """
        return self._default_search_name

    @property
    def grammar_active(self):
        """
        Whether the grammar is enabled and has any active rules.
        :rtype: bool
        """
        return self.grammar.enabled and any(self.grammar.active_rules)

    def reset_all_sequence_rules(self):
        """
        Resetting all SequenceRules, clear the in progress list and reset
        search_name.
        """
        for r in self._dictation_grammar.rules:
            if isinstance(r, SequenceRule):
                r.restart_sequence()

            # Also ensure all rules are now enabled again.
            r.enable()

        # Clear the in-progress list and set search_name back to default.
        self._in_progress_sequence_rules = []

        if self.search_name != self._default_search_name:
            # Unset the search used for in-progress rules. This won't unset the
            # dictation search.
            self.engine.unset_search(self.search_name)

            # Set search name back to default.
            self._search_name = self._default_search_name
            self.engine.set_grammar(self)

    def collect_matching_rules(self, state):
        """
        Collect rules matching state.speech (speech hypothesis) into the given
        state object's rule lists.
        The ProcessingState object can be processed using the GrammarWrapper
        `process` method.
        :type state: ProcessingState
        :rtype: ProcessingState
        """
        speech = state.speech
        if not ((speech or state.speech_is_dictation) or state.use_linked_rules):
            # Check if there are any match rules with dictation expansions
            dict_hyp_required = False
            for rule in self.dictation_grammar.match_rules:
                if dictation_in_expansion(rule.expansion):
                    dict_hyp_required = True
                    break

            if dict_hyp_required:
                dict_hyp = self.engine.get_dictation_hypothesis()
                if dict_hyp:
                    state.speech = dict_hyp
                    state.speech_is_dictation = True

        # Collect matching any in-progress SequenceRules
        if self._in_progress_sequence_rules:
            self._collect_in_progress_sequence_rules(state)

        # Collect matching normal rules
        self._collect_normal_rules(state)
        return state

    def process(self, state, timed_out=False, notify_only=False):
        """
        Process a ProcessingState object from `collect_matching_rules`.

        :param state: ProcessingState
        :param timed_out: used by recognition timeout thread
        :param notify_only: whether to only notify observers, not process
        """
        complete_seq = state.complete_sequence_rules
        if complete_seq:
            words_list = self._generate_words_list(complete_seq[0], True)
            self._process_complete_recognition(words_list, notify_only)

        elif state.in_progress_rules and not timed_out:
            self._notify_partial_recognition(state.in_progress_rules[0])

        elif state.complete_rules:
            words_list = self._generate_words_list(state.complete_rules[0], True)
            self._process_complete_recognition(words_list, notify_only)

    def process_begin(self, fg_window):
        """
        Start the dragonfly grammar processing.
        """
        self.grammar.process_begin(fg_window.executable, fg_window.title,
                                   fg_window.handle)

    def _process_results(self, words):
        """
        Start the dragonfly processing of the speech hypothesis.
        :param words: a sequence of (word, rule_id) 2-tuples (pairs)
        """
        self.engine.log.debug("Grammar %s: received recognition %r." %
                              (self.grammar.name, words))

        words_rules = tuple((text_type(w), r) for w, r in words)
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
            if not r.active:
                continue
            s.initialize_decoding()

            # Iterate each result from decoding state 's' with grammar rule 'r'
            for _ in r.decode(s):
                if s.finished():
                    root = s.build_parse_tree()
                    r.process_recognition(root)
                    return

        self.engine.log.warning("Grammar %s: failed to decode recognition %r."
                                % (self.grammar.name, words))

    def _get_dragonfly_rule(self, rule):
        """
        Get the original dragonfly Rule given a JSGF Rule.
        :param rule: JSGF Rule
        :return: Rule
        """
        if isinstance(rule, LinkedRule):
            linked_rule = rule
        else:
            linked_rule = self._dictation_grammar.get_original_rule(rule)

        df_rule = linked_rule.df_rule
        return df_rule

    def _notify_partial_recognition(self, rule):
        """
        Internal method to notify the engine's next_rule_part observers of a
        partial recognition.
        :type rule: SequenceRule
        """
        self.engine.observer_manager.notify_next_rule_part(
            self._generate_words_list(rule, False)
        )

    def _process_complete_recognition(self, words_list, notify_only):
        """
        Internal method for processing complete recognitions.
        :type words_list: list
        :param notify_only: whether to only notify observers, not process.
        """
        # Notify recognition observers
        self.engine.observer_manager.notify_recognition(words_list)

        # Begin dragonfly processing if appropriate.
        # notify_only is used by the Sphinx engine's training mode.
        if not notify_only:
            try:
                self._process_results(words_list)
            except Exception as e:
                self.engine.log.error("%s: caught Exception while processing "
                                      "recognised words: %s" % (self, e))

        # Clear the in progress list and reset all sequence rules in the grammar.
        self.reset_all_sequence_rules()

        # Switch back to the relevant Pocket Sphinx search
        self.engine.set_grammar(self)

    def _generate_words_list(self, rule, complete_match):
        """
        Generate a words list compatible with dragonfly's processing classes.
        :param rule: JSGF Rule
        :param complete_match: whether all expansions in a SequenceRule must match
        :return: list
        """
        df_rule_id = self.grammar.rules.index(
            self._get_dragonfly_rule(rule)
        )

        if isinstance(rule, SequenceRule) or dictation_in_expansion(rule.expansion):
            words_list = []
            if isinstance(rule, SequenceRule):
                # Used by real speech input and engine.mimic_phrases.
                expansions = rule.expansion_sequence
            else:
                # LinkedRules cannot be partially matched, but this shouldn't
                # happen regardless, so log an error.
                if not rule.was_matched:
                    self.engine.log.error("LinkedRule %s returned an empty words "
                                          "list" % rule)
                    return []

                def matching(x):
                    # Note that Dictation is a subclass of jsgf.Literal so it
                    # doesn't need to be specified here.
                    if isinstance(x, (Literal, RuleRef)) and x.current_match:
                        # All ancestors must also have non-null match values.
                        p = x.parent
                        while p:
                            if not p.current_match:
                                return False
                            p = p.parent
                        return True

                # Initialise the list with the first matching expansion.
                first = find_expansion(rule.expansion, matching)
                expansions = [first]

                if not first:
                    self.engine.log.error("Matching rule %s had no matching "
                                          "expansions" % rule)
                    return []

                # Then add each matchable leaf afterwards. This does what
                # Expansion.matchable_leaves_after does, except that it only looks
                # at leaves in this tree, not referenced ones. This will not work
                # with repetition.
                shallow_leaves = first.root_expansion.collect_leaves(shallow=True)
                first_reached = False
                for leaf in shallow_leaves:
                    if leaf is first:
                        first_reached = True
                        continue
                    elif first_reached and (not first.mutually_exclusive_of(leaf)
                                            and matching(leaf)):
                        expansions.append(leaf)

            # Generate a words list using the match values for each expansion in
            # the list.
            for e in expansions:
                # Use rule IDs compatible with dragonfly's processing classes
                if only_dictation_in_expansion(e):
                    rule_id = 1000000  # dgndictation id
                else:
                    rule_id = df_rule_id

                # If the rule is not completely matched yet and complete_match is
                # False, then use the match values thus far. This should only happen
                # for SequenceRules.
                if not complete_match and e.current_match is None:
                    break

                # Get the words from the expansion's current match
                words = e.current_match.split()
                for word in words:
                    words_list.append((word, rule_id))

        # Non-sequential rules must match completely.
        # These rules shouldn't have any Dictation expansions.
        elif rule.was_matched:
            words_list = [(word, df_rule_id)
                          for word in rule.expansion.current_match.split()]
        else:
            words_list = []

        if not words_list:
            self.engine.log.debug("Rule %s had match '%s', but returned an empty "
                                  "words list"
                                  % (rule, rule.expansion.current_match))

        return words_list

    def _collect_normal_rules(self, state):
        """
        Internal method used to collect normal rules that can be spoken in one
        utterance that match a speech string.
        :type state: ProcessingState
        :rtype: ProcessingState
        """
        # No rules will match None or ""
        if not state.speech:
            return state

        # Find rules of active grammars that match the speech string
        if state.use_linked_rules:
            matching_rules = self._jsgf_grammar.find_matching_rules(state.speech)
            state.complete_rules.extend(matching_rules)
            return state
        else:
            matching_rules = self._dictation_grammar.find_matching_rules(
                state.speech, advance_sequence_rules=False)

        for rule in matching_rules:
            if isinstance(rule, SequenceRule):  # spoken in multiple utterances
                if rule.current_is_dictation_only and not state.speech_is_dictation:
                    # Get a dictation hypothesis
                    dict_hypothesis = self.engine.get_dictation_hypothesis()

                    # Note: if dict_hypothesis is None, then this recognition was
                    # probably invoked by mimic, so don't invalidate the match.
                    if dict_hypothesis:
                        rule.refuse_matches = False
                        rule.matches(dict_hypothesis)

                if rule.has_next_expansion:
                    # Add this rule to the in progress list and enqueue
                    # `rule.set_next()` as a post collection task.
                    state.add_post_collection_task(rule.set_next)
                    self._in_progress_sequence_rules.append(rule)
                    state.in_progress_rules.append(rule)
                else:
                    # The entire sequence has been matched. This rule could only
                    # have had one part to it.
                    state.complete_rules.append(rule)
            else:
                # This rule has been fully recognised.
                state.complete_rules.append(rule)
        return state

    def _collect_in_progress_sequence_rules(self, state):
        """
        Match against SequenceRules that are in progress and add them to the state
        object.
        :type state: ProcessingState
        """
        # No rules will match None or ""
        if not state.speech:
            state.add_post_collection_task(self.reset_all_sequence_rules)
            return state

        # Process the rules using a shallow copy of the in progress list because the
        # original list will be modified
        dict_hypothesis = self.engine.get_dictation_hypothesis()
        for rule in tuple(self._in_progress_sequence_rules):
            # Match the rule with the appropriate hypothesis string.
            if rule.current_is_dictation_only and dict_hypothesis:
                rule.matches(dict_hypothesis)
            else:
                rule.matches(state.speech)

            if not rule.was_matched:
                # Remove and reset the SequenceRule if it didn't match
                state.add_post_collection_task(rule.restart_sequence)
                self._in_progress_sequence_rules.remove(rule)
            elif rule.has_next_expansion:
                # By calling rule.matches, the speech value was stored as the
                # current expansion's current_match value.
                state.add_post_collection_task(rule.set_next)
                self._in_progress_sequence_rules.append(rule)
                state.in_progress_rules.append(rule)
            else:
                # SequenceRule has been completely matched.
                state.complete_rules.append(rule)

        # If the list still has rules, then it needs further processing.
        # Load a JSGF Pocket Sphinx search with just the rules in the list, or
        # switch to the dictation search if there are only dictation rules.
        if self._in_progress_sequence_rules:
            not_in_progress_rules = [r for r in self.dictation_grammar.match_rules
                                     if r not in self._in_progress_sequence_rules]

            # Disable rules in the grammar that aren't in the in-progress list
            for rule in not_in_progress_rules:
                rule.disable()

            # Recursively enable any rules referenced by an in-progress rule
            def enable_referenced(x):
                if isinstance(x, RuleRef):
                    x.rule.enable()

            for rule in self._in_progress_sequence_rules:
                map_expansion(rule.expansion, enable_referenced)

            # Set the search name for a new Pocket Sphinx search.
            # If we use a new name, Pocket Sphinx will keep the grammar's
            # original search around so we can switch back to it later without
            # recompiling and setting it again.
            self._search_name = "%s_narrowed" % self.grammar.name

        def process():
            self.engine.set_grammar(self)
        state.add_post_collection_task(process)
        return state
