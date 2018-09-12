import logging

import jsgf
from jsgf import map_expansion, VoidRef
from jsgf.ext import SequenceRule, dictation_in_expansion

from dragonfly import Grammar, List as DragonflyList, DictList as DragonflyDictList
from dragonfly.grammar.elements import *
from dragonfly.grammar.elements_compound import stuff
from dragonfly.grammar.rule_base import Rule
from dragonfly.parser import Parser, ParserError


class TranslationError(Exception):
    pass


class LinkedGrammar(jsgf.Grammar):
    def __init__(self, name, df_grammar):
        self._df_grammar = df_grammar
        super(LinkedGrammar, self).__init__(name=name)

    @property
    def df_grammar(self):
        """
        Dragonfly grammar that this one was built from.
        :return: Grammar
        """
        return self._df_grammar


class LinkedRule(jsgf.Rule):
    def __init__(self, name, visible, expansion, df_rule):
        self._df_rule = df_rule
        super(LinkedRule, self).__init__(name, visible, expansion)

    @property
    def df_rule(self):
        """
        Dragonfly rule that this one was built from.
        :return: Rule
        """
        return self._df_rule


class PatchedRepeat(jsgf.Repeat):
    """
    Repeat class patched to compile JSGF repeats as "expansion [expansion]*" to
    avoid a bug in Pocket Sphinx with the repeat operator.
    """
    def compile(self, ignore_tags=False):
        super(PatchedRepeat, self).compile()
        compiled = self.child.compile(ignore_tags)
        if self.tag and not ignore_tags:
            return "(%s)[%s]*%s" % (compiled, compiled, self.tag)
        else:
            return "(%s)[%s]*" % (compiled, compiled)


class TranslationState(object):
    """
    Translation state used in building JSGF expansions, rules and grammars from
    dragonfly elements, rules and grammars.
    """
    def __init__(self, element, expansion=None, dependencies=None):
        """
        :type element: ElementBase
        """
        self.element = element
        self._expansion = expansion
        if isinstance(dependencies, list):
            self.dependencies = dependencies
        else:
            self.dependencies = []

        # Used if this object is being used to translate a dragonfly rule.
        self.jsgf_rule = None

    rule_names = property(lambda self: [rule.name for rule in self.dependencies])

    @property
    def expansion(self):
        return self._expansion

    @expansion.setter
    def expansion(self, value):
        # Valid values are an Expansion object or None
        if value is not None and not isinstance(value, jsgf.Expansion):
            raise AttributeError("value must be an Expansion object or None.")

        self._expansion = value


class Translator(object):
    _log = logging.getLogger("dragonfly2jsgf")
    _parser = Parser(stuff, _log)

    def __init__(self):
        # Used to not add duplicate rules in translate_grammar that were already
        # translated in translate_repetition_with_dictation.
        self.expansion_black_list = []

    def translate(self, df_spec):
        element = self._parser.parse(df_spec)
        if not element:
            raise ParserError("Invalid dragonfly spec: %r" % df_spec)

        assert isinstance(element, ElementBase)
        state = TranslationState(element)
        return self.get_jsgf_equiv(state)

    def translate_grammar(self, grammar):
        """
        Translate a dragonfly grammar into a JSGF grammar.
        :type grammar: Grammar
        :return: LinkedGrammar
        """
        self.expansion_black_list = []
        result = LinkedGrammar(grammar.name, grammar)
        for rule in grammar.rules:
            state = self.translate_rule(rule)

            # Add the translated rule and any dependencies found during translation
            result.add_rule(state.jsgf_rule)
            for d in state.dependencies:
                if d not in result.rules:  # don't add the same rule twice
                    result.add_rule(d)

        # Remove any rules with black listed expansions added during translation of
        # repeating dictation rules.
        for rule in result.rules:
            if rule.expansion in self.expansion_black_list:
                result.remove_rule(rule)
        return result

    def translate_rule(self, rule):
        """
        Translate a dragonfly rule into a JSGF rule.
        :type rule: Rule
        :return: TranslationState
        """
        element = rule.element
        state = self.get_jsgf_equiv(TranslationState(element))
        state.jsgf_rule = LinkedRule(rule.name, rule.exported, state.expansion,
                                     rule)
        return state

    def translate_rule_ref(self, state):
        """
        Translate the dragonfly RuleRef object inside the TranslationState
        object by collecting all of the rules as necessary using the
        'dependencies' list.
        :type state: TranslationState
        :return TranslationState
        """
        element = state.element
        if not isinstance(element, RuleRef):
            raise TranslationError("Cannot translate element '%s' as a "
                                   "RuleRef." % state.element)
        name = element.name
        if name is None: name = element.element_tree_string()  # f"RuleRef({referenced_rule_name})"
        if name not in state.rule_names:
            # Make a new equivalent JSGF rule
            state.element = element.rule.element
            self.get_jsgf_equiv(state)
            rule_expansion = state.expansion
            new_rule = jsgf.Rule(name, element.rule.exported, rule_expansion)
            state.element = element
            state.dependencies.append(new_rule)
            state.expansion = jsgf.RuleRef(new_rule)
        else:
            # Use the existing rule
            index = state.rule_names.index(name)
            state.expansion = jsgf.RuleRef(state.dependencies[index])

        return state

    def translate_to_rule(self, rule_name, df_spec, visible=True):
        expansion = self.translate(df_spec).expansion
        return jsgf.Rule(rule_name, visible, expansion)

    @staticmethod
    def translate_list(lst):
        """
        Translate a dragonfly List object into a JSGF rule representing it.
        The returned rule is a HiddenRule because lists can only be referenced by
        rules using ListRef, not spoken directly.
        :type lst: DragonflyList
        :return: HiddenRule
        """
        return jsgf.HiddenRule(lst.name, jsgf.AlternativeSet(*lst))

    @staticmethod
    def translate_dict_list(dict_list):
        """
        Translate a dragonfly DictList object into a JSGF rule representing it.
        The returned rule is a HiddenRule because dict lists can only be referenced
        by rules using DictListRef, not spoken directly.
        :type dict_list: DragonflyDictList
        :return: HiddenRule
        """
        keys = list(dict_list.keys())
        keys.sort()
        return jsgf.HiddenRule(dict_list.name, jsgf.AlternativeSet(*keys))

    @staticmethod
    def translate_list_ref(state):
        """
        Translate the dragonfly ListRef element inside the state object by
        creating a JSGF rule representing the List.

        JSGF has no equivalent for Lists or DictLists, however in the spirit
        of making this engine as full-featured as possible, they can be
        implemented as JSGF rules.

        state.expansion will be set to a JSGF RuleRef for the new rule and the new
        rule itself will be added to the state.dependencies list.

        :type state: TranslationState
        :return: TranslationState
        """
        element = state.element
        if not isinstance(element, (List, ListRef)):
            raise TranslationError("Cannot translate element '%s' as a "
                                   "ListRef." % element)

        # Make a new JSGF rule representing the list and set the appropriate values
        # in the state object
        list_rule = Translator.translate_list(element.list)
        state.dependencies.append(list_rule)
        state.expansion = jsgf.RuleRef(list_rule)
        return state

    @staticmethod
    def translate_dict_list_ref(state):
        """
        Translate the dragonfly DictListRef element inside the state object by
        creating a JSGF rule representing the DictList.

        state.expansion will be set to a JSGF RuleRef for the new rule and the new
        rule itself will be added to the state.dependencies list.

        :type state: TranslationState
        :return: TranslationState
        """
        element = state.element
        if not isinstance(element, (DictList, DictListRef)):
            raise TranslationError("Cannot translate element '%s' as a "
                                   "DictListRef." % element)

        dict_list_rule = Translator.translate_dict_list(element.list)
        state.dependencies.append(dict_list_rule)
        state.expansion = jsgf.RuleRef(dict_list_rule)
        return state

    def _has_dictation_descendant(self, element):
        """
        Find if there is a Dictation element in an element tree. This will also
        find Dictation elements in any referenced rule's tree.
        :return: list
        """
        result = False
        if isinstance(element, Dictation):
            result = True
        elif isinstance(element, RuleRef):
            result = result or self._has_dictation_descendant(element.rule.element)
        else:
            for child in element.children:
                result = result or self._has_dictation_descendant(child)
        return result

    def translate_repetition_with_dictation(self, state):
        """
        Translate a dragonfly Repetition element that has at least one Dictation
        descendant.
        :type state: TranslationState
        :return: TranslationState
        """
        element = state.element

        # Calculate the equivalent JSGF expansion for the first child and ignore the
        # rest (if any); such children are used for min/max limits on the number of
        # repetitions. These limits doesn't make much sense for Dictation
        # functionality that has required utterance pauses. Any min/max limit is
        # handled by the engine on a JSGF rule level instead of here.
        state.element = state.element.children[0]
        self.get_jsgf_equiv(state)
        child = state.expansion

        # Switch element back to the Repetition
        state.element = element

        # Process rule references in the expansion tree with dictation
        def process(x):
            if isinstance(x, jsgf.RuleRef) and dictation_in_expansion(x):
                # Skip the RuleRef and use the rule's expansion tree instead
                if x.parent:
                    # If there is a parent, replace x with the referenced rule's
                    # expansion in the parent's children list.
                    i = x.parent.children.index(x)
                    x.parent.children.remove(x)
                    x.parent.children.insert(i, x.rule.expansion)
                x.referenced_rule.expansion.parent = x.parent

                # The rule is no longer a dependency and should not be included in
                # the final grammar
                state.dependencies.remove(x.referenced_rule)

                # In case it was translated before this method, blacklist it!
                self.expansion_black_list.append(x.referenced_rule.expansion)

                # Replace the original child if necessary
                if x is child:
                    state.expansion = x.referenced_rule.expansion

        map_expansion(child, process)

        # Wrap the new expansion in a Repeat
        state.expansion = PatchedRepeat(state.expansion)
        return state

    def get_jsgf_equiv(self, state):
        """
        Take a TranslationState object containing a dragonfly element
        return the same object with the 'expansion' member set to the
        equivalent JSGF expansion object.
        :type state: TranslationState
        :return TranslationState
        """
        element = state.element

        def get_equiv_children():
            children = []
            for child in state.element.children:
                state.element = child
                self.get_jsgf_equiv(state)
                children.append(state.expansion)
            return children

        if isinstance(element, Literal):  # Literal == word list
            text = " ".join(element.words)
            state.expansion = jsgf.Literal(text)

        elif isinstance(element, (RuleRef, Rule)):
            # Translate the dragonfly rule reference
            self.translate_rule_ref(state)

        # DictListRef should be checked before ListRef because it is a subclass
        elif isinstance(element, (DictListRef, DictList)):
            self.translate_dict_list_ref(state)

        elif isinstance(element, (ListRef, List)):
            self.translate_list_ref(state)

        elif isinstance(element, Dictation):
            # A Sphinx decoder for handling dictation will be prepared and used
            # when necessary.
            state.expansion = jsgf.ext.Dictation()

        elif isinstance(element, Impossible):
            # VoidRef is the equivalent of dragonfly's Impossible element.
            # It is also automatically used by pyjsgf if an expansion that should
            # have at least one child (e.g. Sequence/Repeat) doesn't have any at
            # compile time.
            state.expansion = VoidRef()

        elif element.children == ():  # improbable ElementBase case
            state.expansion = jsgf.Expansion([])

        # Repetition should be checked before Sequence because it is a subclass
        elif isinstance(element, Repetition):
            # Repetition should have at least one child
            assert len(state.element.children) > 0

            if self._has_dictation_descendant(element):
                self.translate_repetition_with_dictation(state)
            else:
                # Translate the first child only. The second child is of the form:
                # [first_child [first_child ... first_child ] ... ]
                # This is how matching a limited number of repetitions is done.
                # Limitation (min/max) values for Repetition elements are ignored
                # for the Sphinx engine for the moment.
                equiv_child = get_equiv_children()[0]
                state.expansion = PatchedRepeat(equiv_child)

        elif isinstance(element, Sequence):
            state.expansion = jsgf.Sequence(*get_equiv_children())

        elif isinstance(element, Alternative):
            if len(state.element.children) == 1:
                # Skip redundant (1 child) alternatives
                state.element = state.element.children[0]
                self.get_jsgf_equiv(state)
            else:
                state.expansion = jsgf.AlternativeSet(*get_equiv_children())

        elif isinstance(element, Optional):
            equiv_children = get_equiv_children()
            if len(equiv_children) != 1:
                raise TranslationError("Optional grouping may only have 1 child.")
            state.expansion = jsgf.OptionalGrouping(equiv_children[0])

        return state
