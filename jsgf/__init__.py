"""
JSpeech Grammar Format module for Python
'The JSpeech Grammar Format (JSGF) is a platform-independent,vendor-independent
textual representation of grammars for use in speech recognition. Grammars are
used by speech recognizers to determine what the recognizer should listen for,
and so describe the utterances a user may say. JSGF adopts the style and
conventions of the JavaTM Programming Language in addition to use of
traditional grammar notations.'
See the specification here: https://www.w3.org/TR/jsgf/

This module supports compiling JSGF grammars using custom rules, imports and
expansions, such as the Kleene Star, optional and required groupings.

(hello <name>

"""

from expansions import AlternativeSet
from expansions import ExpansionError
from expansions import Expansion
from expansions import KleeneStar
from expansions import Literal
from expansions import OptionalGrouping
from expansions import Repeat
from expansions import RequiredGrouping
from expansions import RuleRef
from expansions import Sequence

from grammar import Grammar
from grammar import Import

from rules import Rule
from rules import PublicRule
from rules import HiddenRule
