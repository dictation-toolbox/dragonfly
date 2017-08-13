"""
Classes for compiling JSpeech Grammar Format rules
"""
import re
import jsgf


class Rule(object):
    def __init__(self, name, visible, expansion):
        """
        :type name: str
        :type visible: bool
        :param expansion:
        """
        self.name = name
        self.visible = visible
        self.expansion = expansion
        self._matching_regex = None

    def compile(self, ignore_tags=False):
        """
        Compile this rule's expansion tree and return the result.
        Set ignore_tags to True to not include expansion tags in the result.
        :type ignore_tags: bool
        :rtype: str
        """
        result = "<%s> = %s;" % (self.name,
                                 self.expansion.compile(ignore_tags))

        if self.visible:
            return "public %s" % result
        else:
            return result

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           self.expansion)

    def matches(self, speech):
        """
        Whether speech matches this rule.
        :type speech: str
        """
        if not self._matching_regex:
            self._tweak_literals(self.expansion)
            self._matching_regex = re.compile(
                self.expansion.matching_regex() + r"\Z")

        if self._matching_regex.match(speech.lower()):
            return True
        else:
            return False

    @property
    def dependencies(self):
        """
        Get the rules dependent on this on, i.e. the dependencies
        :rtype: set
        """
        def collect_referenced_rules(expansion, result):
            """
            Recursively collect every RuleRef object's Rule in an Expansion tree and every
            referenced rule in the referenced rule's Expansion tree and so on.
            :type expansion: jsgf.Expansion
            :type result: set
            """
            if isinstance(expansion, jsgf.RuleRef):
                result.add(expansion.rule)
                collect_referenced_rules(expansion.rule.expansion, result)
            else:
                for child in expansion.children:
                    collect_referenced_rules(child, result)

            return result
        return collect_referenced_rules(self.expansion, set())

    @staticmethod
    def _tweak_literals(expansion):
        """
        Set up Literal Expansions so that their regular expressions
        can be calculated correctly.
        :type expansion: Expansion
        """
        def find_first_literal(expansion, parent):
            """
            Recursively find the first Literal in an Expansion tree
            or in a referenced rule's Expansion tree.
            Also return the parent Expansion for handling special cases.
            :param parent:
            :type expansion: jsgf.Expansion
            """
            # Check any referenced rules first
            result = None
            if isinstance(expansion, jsgf.RuleRef):
                result = find_first_literal(expansion.rule.expansion, None)

            elif isinstance(expansion, jsgf.Literal):
                result = expansion, parent
            else:
                for child in expansion.children:
                    result = find_first_literal(child, expansion)
                    if result:
                        break

            return result

        (first_literal, parent) = find_first_literal(expansion, None)

        # The first Literal in an Expansion tree shouldn't have
        # whitespace before it
        if first_literal:
            first_literal.whitespace_before_literal = False

        # Handle the special case of AlternativeSet as a parent:
        # Every Literal in an AlternativeSet with the first literal
        # must also have no leading whitespace match before it,
        # otherwise there will be issues matching the rule to any other
        #  Literal.
        if isinstance(parent, jsgf.AlternativeSet):
            for child in parent.children:
                if isinstance(child, jsgf.Literal):
                    child.whitespace_before_literal = False


class PublicRule(Rule):
    def __init__(self, name, expansion):
        super(PublicRule, self).__init__(name, True, expansion)


class HiddenRule(Rule):
    def __init__(self, name, expansion):
        super(HiddenRule, self).__init__(name, False, expansion)
