from lark import Lark, Transformer
from ..grammar.elements_basic import Literal, Optional, Sequence, Alternative, Empty
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

spec_parser = Lark.open(os.path.join(dir_path, "grammar.lark"),
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

