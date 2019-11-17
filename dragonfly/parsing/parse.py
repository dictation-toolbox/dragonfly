from lark import Lark, Transformer
from ..grammar.elements_basic import Literal, Optional, Sequence, Alternative, Empty
import os

grammar = r"""
?start: alternative

// ? means that the rule will be inlined iff there is a single child
?alternative: sequence ("|" sequence)*
?sequence: single*

?single: WORD+               -> literal
      | "<" WORD ">"         -> reference
      | "[" alternative "]"  -> optional
      | "(" alternative ")"

// Match anything which is not whitespace or a control character,
// we will let the engine handle invalid words
WORD: /[^\s\[\]<>|()]+/

%import common.WS_INLINE
%ignore WS_INLINE
"""

spec_parser = Lark(
    grammar,
    parser="lalr"
)

class ParseError(Exception):
    pass

class CompoundTransformer(Transformer):
    """
        Visits each node of the parse tree starting with the leaves
        and working up, replacing lark Tree objects with the
        appropriate dragonfly classes.
    """

    def __init__(self, extras=None, *args, **kwargs):
        self.extras = extras or {}
        Transformer.__init__(self, *args, **kwargs)

    def optional(self, args):
        return Optional(args[0])

    def literal(self, args):
        return Literal(" ".join(args))

    def sequence(self, args):
        return Sequence(args)

    def alternative(self, args):
        return Alternative(args)

    def reference(self, args):
        ref = args[0]
        try:
            return self.extras[ref]
        except KeyError:
            raise Exception("Unknown reference name %r" % (str(ref)))

