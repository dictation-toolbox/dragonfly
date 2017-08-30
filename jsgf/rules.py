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

        # Handle the object passed in as an expansion
        self.expansion = jsgf.Expansion.handle(expansion)

        self._matching_regex = re.compile(
            self.expansion.matching_regex() + r"\Z")
        self._reference_count = 0

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
        # Insert whitespace before 'speech' to match regex properly.
        if self._matching_regex.match(" " + speech.lower()):
            return True
        else:
            return False

    @property
    def dependencies(self):
        """
        The set of rules which this rule directly and indirectly references.
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
                if expansion.rule not in result:  # prevent cycles
                    result.add(expansion.rule)
                    collect_referenced_rules(expansion.rule.expansion, result)
            else:
                for child in expansion.children:
                    collect_referenced_rules(child, result)

            return result
        return collect_referenced_rules(self.expansion, set())

    @property
    def reference_count(self):
        return self._reference_count

    @reference_count.setter
    def reference_count(self, value):
        assert isinstance(value, int) and value >= 0
        self._reference_count = value


class PublicRule(Rule):
    def __init__(self, name, expansion):
        super(PublicRule, self).__init__(name, True, expansion)


class HiddenRule(Rule):
    def __init__(self, name, expansion):
        super(HiddenRule, self).__init__(name, False, expansion)
