"""
Classes for compiling and importing JSpeech Grammar Format grammars
"""

from .rules import Rule, PublicRule
from .expansions import RuleRef, AlternativeSet


class GrammarError(Exception):
    pass


class Import(object):
    def __init__(self, name):
        self.name = name

    def compile(self):
        return "import <%s>;" % self.name

    def __str__(self):
        return "Import(%s)" % self.name


class Grammar(object):
    def __init__(self, name="default"):
        self.name = name
        self._rules = []
        self._imports = []

    def compile_grammar(self, charset_name="UTF-8", language_name="en",
                        jsgf_version="1.0"):
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
        compiled_lines = self.compile_grammar(charset_name, language_name,
                                              jsgf_version).splitlines()
        with open(file_path, "w+") as f:
            f.writelines(compiled_lines)

    def compile_with_root_public_rule(self, charset_name="UTF-8",
                                      language_name="en",
                                      jsgf_version="1.0"):
        """
        Compile the grammar with one public "root" rule containing rule
        references in an alternative set to every other rule as such:
        public <root> = (<rule1>|<rule2>|..|<ruleN>);
        <rule1> = ...;
        <rule2> = ...;
        .
        .
        .
        <ruleN> = ...;
        :type charset_name: str
        :type language_name: str
        :type jsgf_version: str
        :rtype: str
        """
        # Make every rule not public and make RuleRef objects for each
        rule_refs = []
        for rule in self.rules:
            rule.visible = False
            rule_refs.append(RuleRef(rule))

        # Temporarily add a new public rule as the first rule
        # that matches any rule once.
        temp_root = PublicRule("root", AlternativeSet(*rule_refs))
        self._rules.insert(0, temp_root)

        compiled = self.compile_grammar(charset_name, language_name,
                                    jsgf_version)
        self._rules.remove(temp_root)
        return compiled


    @property
    def rules(self):
        """
        Get the rules added to this grammar.
        :rtype: list
        """
        return self._rules


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
        if not isinstance(_import, Import):
            raise TypeError("object '%s' was not a JSGF Import object" % _import)
        self._rules.append(_import)

    def find_matching_rules(self, speech):
        matching = []
        for rule in self.rules:
            if rule.matches(speech):
                matching.append(rule)
        return matching
