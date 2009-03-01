#
# This file is part of Dragonfly.
# (c) Copyright 2007, 2008 by Christo Butcher
# Licensed under the LGPL.
#
#   Dragonfly is free software: you can redistribute it and/or modify it 
#   under the terms of the GNU Lesser General Public License as published 
#   by the Free Software Foundation, either version 3 of the License, or 
#   (at your option) any later version.
#
#   Dragonfly is distributed in the hope that it will be useful, but 
#   WITHOUT ANY WARRANTY; without even the implied warranty of 
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU 
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public 
#   License along with Dragonfly.  If not, see 
#   <http://www.gnu.org/licenses/>.
#

#---------------------------------------------------------------------------
import dragonfly.log
from .log      import get_log
from .config   import Config, Section, Item

#---------------------------------------------------------------------------
from .grammar.grammar_base       import Grammar
from .grammar.grammar_connection import ConnectionGrammar
from .grammar.rule_base          import Rule
from .grammar.rule_compound      import CompoundRule
from .grammar.rule_mapping       import MappingRule
from .grammar.elements  import (ElementBase, Sequence, Alternative,
                                         Optional, Repetition, Literal,
                                         ListRef, DictListRef, Dictation,
                                         RuleRef, Empty, Compound, Choice)
from .grammar.context   import Context, AppContext
from .grammar.list      import ListBase, List, DictList
from .grammar.wordinfo  import Word, FormatState

#---------------------------------------------------------------------------
from .engines.engine    import get_engine

#---------------------------------------------------------------------------
from .actions.actions   import (ActionBase, Key, Text, Paste,
                                            Pause, Mimic, WaitWindow)
from .actions.keyboard  import Typeable, Keyboard
from .actions.typeables import typeables

#---------------------------------------------------------------------------
from .windows.window    import Window
from .windows.monitor   import Monitor
from .windows.clipboard import Clipboard

#---------------------------------------------------------------------------
import dragonfly.grammar.number as _number
Integer     = _number.Integer
IntegerRef  = _number.IntegerRef
Digits      = _number.Digits
DigitsRef   = _number.DigitsRef
Number      = _number.Number
NumberRef   = _number.NumberRef
