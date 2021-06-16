from lark import Lark, Transformer

from dragonfly.grammar.elements_basic import (Literal, Optional, Sequence,
                                              Alternative, Empty)

grammar_string = r"""
?start: alternative

// ? means that the rule will be inlined iff there is a single child
?alternative: sequence ("|" sequence)*
?sequence: single*
         | sequence "{" WORD "}"  -> special

?single: WORD+               -> literal
      | "<" WORD ">"         -> reference
      | "[" alternative "]"  -> optional
      | "(" alternative ")"

// Match anything which is not whitespace or a control character,
// we will let the engine handle invalid words
WORD: /[^\s\[\]<>|(){}]+/

%import common.WS_INLINE
%ignore WS_INLINE
"""

spec_parser = Lark(
    grammar_string,
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

    def special(self, args):
        child, specifier = args
        if '=' in specifier:
            name, value = specifier.split('=')

            # Try to convert the value to a bool, None or a float.
            if value in ['True', 'False']:
                value = bool(value)
            elif value == 'None':
                value = None
            else:
                try:
                    value = float(value)
                except ValueError:
                    # Conversion failed, value is just a string.
                    pass
        else:
            name, value = specifier, True

        if name in ['weight', 'w']:
            child.weight = float(value)
        elif name in ['test_special']:
            child.test_special = value
        else:
            raise ParseError("Unrecognized special specifier: {%s}" %
                             specifier)

        return child
