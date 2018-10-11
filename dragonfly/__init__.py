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
from .config            import Config, Section, Item
from .error             import DragonflyError

#---------------------------------------------------------------------------
from .engines           import get_engine, EngineError, MimicFailure

#---------------------------------------------------------------------------
from .grammar.grammar_base       import Grammar
from .grammar.grammar_connection import ConnectionGrammar
from .grammar.rule_base          import Rule
from .grammar.rule_compound      import CompoundRule
from .grammar.rule_mapping       import MappingRule
from .grammar.elements  import (ElementBase, Sequence, Alternative,
                                Optional, Repetition, Literal,
                                ListRef, DictListRef, Dictation,
                                RuleRef, RuleWrap, Empty, Compound, Choice)

from .grammar.context   import Context, AppContext
from .grammar.list      import ListBase, List, DictList
from .grammar.recobs    import (RecognitionObserver, RecognitionHistory,
                                PlaybackHistory)

#from .grammar.number    import (Integer, IntegerRef, Digits, DigitsRef,
#                                Number, NumberRef)

#---------------------------------------------------------------------------

from .actions           import (ActionBase, DynStrActionBase, ActionError,
                                Repeat, Key, Text, Mouse, Paste, Pause,
                                Mimic, Playback, WaitWindow, FocusWindow,
                                Function, StartApp, BringApp, PlaySound,
                                Typeable, Keyboard, typeables,
                                KeyboardInput, MouseInput, HardwareInput,
                                make_input_array, send_input_array
                                )

#---------------------------------------------------------------------------

from .util              import Clipboard

#---------------------------------------------------------------------------

from .windows.rectangle import Rectangle, unit
from .windows.point     import Point
from .windows           import Window
from .windows           import Monitor, monitors

#---------------------------------------------------------------------------
from .language          import (Integer, IntegerRef,
                                Digits, DigitsRef,
                                Number, NumberRef)
