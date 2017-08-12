"""
Classes for compiling JSpeech Grammar Format expansions
"""
from rules import Rule


class ExpansionError(Exception):
    pass


class Expansion(object):
    """
    Expansion base class
    """
    def __init__(self, children):
        self._tag = None
        if isinstance(children, (tuple, list)):
            self._children = children
        else:
            raise TypeError("'children' must be a list or tuple")

    def __add__(self, other):
        return self + other

    children = property(lambda self: self._children)

    def compile(self, ignore_tags=False):
        if self.tag and not ignore_tags:
            return self.tag
        else:
            return ""

    @property
    def tag(self):
        # If the tag is set, return it with a space before it
        # Otherwise return the empty string
        if self._tag:
            return " " + self._tag
        else:
            return ""

    @tag.setter
    def tag(self, value):
        """
        Sets the tag for the expansion.
        :type value: str
        """
        # Escape '{', '}' and '\' so that tags will be processed
        # properly if they have those characters.
        # This is suggested in the JSGF specification.
        assert isinstance(value, str)
        escaped = value.replace("{", "\\{") \
            .replace("}", "\\}") \
            .replace("\\", "\\\\")
        self._tag = "{ %s }" % escaped

    @staticmethod
    def handle(e):
        if isinstance(e, str):
            return Literal(e)
        elif isinstance(e, Expansion):
            return e
        else:
            raise TypeError("can only take strings or Expansions")

    def matching_regex(self):
        """
        A regex string for matching this expansion.
        :return: str
        """
        return ""

    def __str__(self):
        descendants = ", ".join(["%s" % c for c in self.children])
        if self.tag:
            return "%s(%s) with tag '%s'" % (self.__class__.__name__,
                                             descendants,
                                             self.tag)
        else:
            return "%s(%s)" % (self.__class__.__name__,
                               descendants)


class Sequence(Expansion):
    def __init__(self, *expansions):
        self.expansions = map(self.handle, expansions)
        super(Sequence, self).__init__(expansions)

    def compile(self, ignore_tags=False):
        seq = " ".join([
            e.compile(ignore_tags) for e in self.expansions
        ])

        # Return the sequence and the tag if there is one
        if self.tag and not ignore_tags:
            return "%s%s" % (seq, self.tag)
        else:
            return seq

    def matching_regex(self):
        """
        A regex string for matching this expansion.
        :return: str
        """
        return "".join([
            e.matching_regex() for e in self.expansions
        ])


class Literal(Expansion):
    def __init__(self, text):
        self.text = text
        self._whitespace_before_literal = True
        super(Literal, self).__init__([])

    def __str__(self):
        return "%s('%s')" % (self.__class__.__name__, self.text)

    @property
    def whitespace_before_literal(self):
        """
        Changes if whitespace is inserted before the
        Literal's text in the matching_regex method.
        :return: bool
        """
        return self._whitespace_before_literal

    @whitespace_before_literal.setter
    def whitespace_before_literal(self, value):
        self._whitespace_before_literal = value

    def compile(self, ignore_tags=False):
        if self.tag and not ignore_tags:
            return "%s%s" % (self.text, self.tag)
        else:
            return self.text

    def matching_regex(self):
        """
        A regex string for matching this expansion.
        :return: str
        """
        # Raise an error if whitespace_before_literal isn't set
        # because it is necessary to have more context here.
        if self._whitespace_before_literal is None:
            raise ExpansionError("cannot accurately generate regex for "
                                 "Literals without "
                                 "'whitespace_before_literal' set.")

        # Selectively escape certain characters because this text will
        # be used in a regular expression pattern string.
        #
        escaped = self.text.replace(".", r"\.")

        # Also make everything lowercase and allow matching 1 or more
        # whitespace character between words
        words = escaped.lower().split()
        if self.whitespace_before_literal:
            return "\s+%s" % "\s+".join(words)
        else:
            return "\s+".join(words)


class RuleRef(Expansion):
    def __init__(self, rule):
        """
        Class for referencing another rule from a rule.
        :type rule: RuleBase
        """
        if not isinstance(rule, Rule):
            raise TypeError("'rule' parameter for RuleRef must be a JSGF rule.")
        self.rule = rule
        super(RuleRef, self).__init__([])

    def compile(self, ignore_tags=False):
        if self.tag and not ignore_tags:
            return "<%s>%s" % (self.rule.name, self.tag)
        else:
            return "<%s>" % self.rule.name

    def matching_regex(self):
        return self.rule.expansion.matching_regex()


class KleeneStar(Expansion):
    """
    JSGF Kleene star operator for allowing zero
    or more repeats of an expansion. For example:
    <kleene> = (please)* don't crash;
    """
    def __init__(self, expansion):
        """
        :type expansion: Expansion
        """
        self.expansion = self.handle(expansion)
        super(KleeneStar, self).__init__([expansion])

    def compile(self, ignore_tags=False):
        compiled = self.expansion.compile(ignore_tags)
        if self.tag and not ignore_tags:
            return "(%s)*%s" % (compiled, self.tag)
        else:
            return "(%s)*" % compiled

    def matching_regex(self):
        """
        A regex string for matching this expansion.
        :return: str
        """
        return "(%s)*" % self.expansion.matching_regex()


class Repeat(Expansion):
    """
    JSGF plus operator for allowing one
    or more repeats of an expansion. For example:
    <kleene> = (please)+ don't crash;
    """
    def __init__(self, expansion):
        """
        :type expansion: Expansion
        """
        self.expansion = self.handle(expansion)
        super(Repeat, self).__init__([expansion])

    def compile(self, ignore_tags=False):
        compiled = self.expansion.compile(ignore_tags)
        if self.tag and not ignore_tags:
            return "(%s)+%s" % (compiled, self.tag)
        else:
            return "(%s)+" % compiled

    def matching_regex(self):
        """
        A regex string for matching this expansion.
        :return: str
        """
        return "(%s)+" % self.expansion.matching_regex()


class OptionalGrouping(Expansion):
    def __init__(self, expansion):
        """
        Optional grouping of an expansion.
        :type expansion: Expansion
        """
        self.expansion = self.handle(expansion)
        super(OptionalGrouping, self).__init__([expansion])

    def compile(self, ignore_tags=False):
        compiled = self.expansion.compile(ignore_tags)
        if self.tag and not ignore_tags:
            return "[%s]%s" % (compiled, self.tag)
        else:
            return "[%s]" % compiled

    def matching_regex(self):
        """
        A regex string for matching this expansion.
        :return: str
        """
        return "(%s)?" % self.expansion.matching_regex()


class RequiredGrouping(Expansion):
    def __init__(self, *expansions):
        self.expansions = map(self.handle, expansions)
        super(RequiredGrouping, self).__init__(expansions)

    def compile(self, ignore_tags=False):
        grouping = "".join([
            e.compile(ignore_tags) for e in self.expansions
        ])

        if self.tag and not ignore_tags:
            return "(%s%s)" % (grouping, self.tag)
        else:
            return "(%s)" % grouping

    def matching_regex(self):
        """
        A regex string for matching this expansion.
        :return: str
        """
        grouping = "".join([
            e.matching_regex() for e in self.expansions
        ])
        return "(%s)" % grouping


class AlternativeSet(Expansion):
    def __init__(self, *expansions):
        self._weights = None
        self.expansions = map(self.handle, expansions)
        super(AlternativeSet, self).__init__(self.expansions)

    @property
    def weights(self):
        return self._weights

    @weights.setter
    def weights(self, value):
        self._weights = value

    def compile(self, ignore_tags=False):
        if self.weights:
            # Create a string with w=weight and e=compiled expansion
            # such that:
            # /<w 0>/ <e 0> | ... | /<w n-1>/ <e n-1>
            alt_set = "|".join([
                "/%f/ %s" % (self.weights[i],
                             e.compile(ignore_tags))
                for i, e in enumerate(self.expansions)
            ])
        else:
            # Or do the same thing without the weights
            alt_set = "|".join([
                e.compile(ignore_tags) for e in self.expansions
            ])

        if self.tag and not ignore_tags:
            return "(%s%s)" % (alt_set, self.tag)
        else:
            return "(%s)" % alt_set

    def matching_regex(self):
        """
        A regex string for matching this expansion.
        :return: str
        """
        alt_set = "|".join([
            "(%s)" % e.matching_regex() for e in self.expansions
        ])
        return "(%s)" % alt_set
