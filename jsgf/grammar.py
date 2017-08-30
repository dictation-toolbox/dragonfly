"""
Classes for compiling and importing JSpeech Grammar Format grammars
"""

from .rules import Rule, PublicRule, HiddenRule
from .expansions import RuleRef, AlternativeSet


class GrammarError(Exception):
    pass


class Import(object):
    def __init__(self, name):
        self.name = name

    def compile(self):
        return "import <%s>;" % self.name

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.name)


class Grammar(object):
    def __init__(self, name="default"):
        self.name = name
        self._rules = []
        self._imports = []

    def compile_grammar(self, charset_name="UTF-8", language_name="en",
                        jsgf_version="1.0"):
        """
        Compile this grammar's imports and rules into a string that can be recognized by a
        JSGF parser.
        :param charset_name:
        :param language_name:
        :param jsgf_version:
        :rtype: str
        """
        grammar_header = "#JSGF V%s %s %s;\n" % (jsgf_version,
                                                 charset_name,
                                                 language_name)
        result = grammar_header
        result += "grammar %s;\n" % self.name

        for i in self._imports:
            result += "%s\n" % i.compile()

        for r in self._rules:
            result += "%s\n" % r.compile()

        return result

    def compile_to_file(self, file_path, charset_name="UTF-8",
                        language_name="en", jsgf_version="1.0"):
        """
        Compile this grammar by calling compile_grammar and write the result to the
        specified file.
        :param file_path:
        :param charset_name:
        :param language_name:
        :param jsgf_version:
        :return:
        """
        compiled_lines = self.compile_grammar(charset_name, language_name,
                                              jsgf_version).splitlines()
        with open(file_path, "w+") as f:
            f.writelines(compiled_lines)

    def recreate_with_root_public_rule(self):
        """
        Create a new grammar with one public "root" rule containing rule references
        in an alternative set to every other rule as such:
        public <root> = (<rule1>|<rule2>|..|<ruleN>);
        <rule1> = ...;
        <rule2> = ...;
        .
        .
        .
        <ruleN> = ...;
        :rtype: RootGrammar
        """
        return RootGrammar(self.rules)

    @property
    def rules(self):
        """
        Get the rules added to this grammar.
        :rtype: list
        """
        return self._rules

    visible_rules = property(
        lambda self: filter(lambda rule: True if rule.visible else False, self.rules),
        doc="""
        The rules in this grammar which have the visible attribute set to True.
        :rtype: list
        """
    )

    rule_names = property(
        lambda self: map(lambda rule: rule.name, self.rules),
        doc="""
        The rule names of each rule in this grammar.
        :rtype: list
        """
    )

    def __str__(self):
        rules = ", ".join(["%s" % rule for rule in self.rules])
        return "Grammar(%s) with rules: %s" % (self.name, rules)

    def add_rules(self, *rules):
        for r in rules:
            self.add_rule(r)

    def add_imports(self, *imports):
        for i in imports:
            self.add_import(i)

    def add_rule(self, rule):
        if not isinstance(rule, Rule):
            raise TypeError("object '%s' was not a JSGF Rule object" % rule)
        self._rules.append(rule)

    def add_import(self, _import):
        """
        Add an import for another JSGF grammar file.
        :type _import: Import
        """
        if not isinstance(_import, Import):
            raise TypeError("object '%s' was not a JSGF Import object" % _import)
        self._rules.append(_import)

    def find_matching_rules(self, speech):
        """
        Find each visible rule in this grammar that matches the 'speech' string.
        :type speech: str
        :return: list
        """
        matching = []
        for rule in self.visible_rules:
            if rule.matches(speech):
                matching.append(rule)
        return matching

    def remove_rule(self, rule_name):
        """
        Remove a rule from this grammar.
        :param rule_name:
        :type rule_name: str
        """
        if not isinstance(rule_name, str):
            raise TypeError("object '%s' was not a string" % rule_name)

        if rule_name not in self.rule_names:
            raise GrammarError("'%s' is not a rule in Grammar '%s'" % (rule_name, self))

        # Check if rule with name 'rule_name' is a dependency of another rule in this
        # grammar.
        i = self.rule_names.index(rule_name)
        rule = self._rules[i]
        if rule.reference_count > 0:
            raise GrammarError("Cannot remove rule '%s' as it is referenced by a RuleRef "
                               "object in another rule." % rule_name)

        self._rules.pop(i)


class RootGrammar(Grammar):
    """
    A grammar with one public "root" rule containing rule references in an alternative set
    to every other rule as such:
    public <root> = (<rule1>|<rule2>|..|<ruleN>);
    <rule1> = ...;
    <rule2> = ...;
    .
    .
    .
    <ruleN> = ...;
    """
    def __init__(self, rules=None, name="root"):
        super(RootGrammar, self).__init__(name)
        if rules is None:
            rules = []

        # Recreate each Public (visible) rule as a HiddenRule instead and make RuleRef
        # objects for each new rule.
        new_rules = []
        rule_refs = []
        for rule in rules:
            if rule.visible:
                rule = HiddenRule(rule.name, rule.expansion)
                rule_refs.append(RuleRef(rule))

            new_rules.append(rule)

        # Add a new public rule as the first rule that matches any rule exactly once.
        self._root_rule = PublicRule("root", AlternativeSet(*rule_refs))
        self._rule_refs = rule_refs
        self._rules.append(self._root_rule)
        for rule in new_rules:
            self._rules.append(rule)

        # Keep references to the original rules for matching against later
        self._match_rules = map(lambda r: r, rules)  # use a new list

    def add_rule(self, rule):
        """
        Add a rule to the grammar and add it as an alternative in the root rule if it is
        visible.
        :param rule:
        :type rule: Rule
        """
        new_rule = HiddenRule(rule.name, rule.expansion)
        super(RootGrammar, self).add_rule(new_rule)

        # Add the original rule to the match_rules list
        self._match_rules.append(rule)

        # Add new_rule as an alternative in the root rule only if rule was originally visible
        if rule.visible:
            self._rule_refs.append(RuleRef(new_rule))
            self._root_rule.expansion = AlternativeSet(*self._rule_refs)

    def remove_rule(self, rule_name):
        """
        Remove a rule from the grammar and the alternative set in the root rule if it is
        visible.
        Raise an error if the rule to be removed is the last visible rule or a rule that
        another rule is dependent on.
        :raises: GrammarError
        :param rule_name:
        :type rule_name: str
        """
        # Check if this rule is the last visible rule
        rule_ref_names = map(lambda r: r.rule.name, self._rule_refs)
        if rule_name in rule_ref_names and len(rule_ref_names) == 1:
            raise GrammarError("cannot remove the last visible rule from RootGrammar: '%s'."
                               % self)

        if rule_name == self._root_rule.name:
            raise GrammarError("cannot remove the root rule from RootGrammar.")

        # Find and remove the corresponding RuleRef object
        i = rule_ref_names.index(rule_name)
        self._rule_refs.pop(i)

        # Also remove the rule from the match_rules list used for matching
        match_rule_names = map(lambda r: r.name, self._match_rules)
        j = match_rule_names.index(rule_name)
        self._match_rules.pop(j)

        # Modify the root rule appropriately
        self._root_rule.expansion = AlternativeSet(*self._rule_refs)

        super(RootGrammar, self).remove_rule(rule_name)

    def compile_grammar(self, charset_name="UTF-8", language_name="en",
                        jsgf_version="1.0"):
        if len(self._rule_refs) == 0:
            raise GrammarError("Root grammar must take at least one Public or visible rule.")

        return super(RootGrammar, self).compile_grammar(charset_name, language_name, jsgf_version)

    def find_matching_rules(self, speech):
        """
        Find each visible rule passed to the grammar that matches the 'speech' string.
        :type speech: str
        :return: list
        """
        matching = []
        for rule in self._match_rules:
            if rule.visible and rule.matches(speech):
                matching.append(rule)
        return matching
