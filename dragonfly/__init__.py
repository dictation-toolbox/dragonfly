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

import sys

# --------------------------------------------------------------------------
from .config            import Config, Section, Item
from .error             import DragonflyError, GrammarError

# --------------------------------------------------------------------------
from .engines           import (get_engine, EngineError, MimicFailure,
                                get_current_engine)

# --------------------------------------------------------------------------
from .grammar.grammar_base       import Grammar
from .grammar.grammar_connection import ConnectionGrammar
from .grammar.rule_base          import Rule
from .grammar.rule_basic         import BasicRule
from .grammar.rule_compound      import CompoundRule
from .grammar.rule_mapping       import MappingRule
from .grammar.elements  import (ElementBase, Sequence, Alternative,
                                Optional, Repetition, Literal,
                                ListRef, DictListRef, Dictation, Modifier,
                                RuleRef, RuleWrap, Compound, Choice,
                                Empty, Impossible)

from .grammar.context   import Context, AppContext, FuncContext
from .grammar.list      import ListBase, List, DictList
from .grammar.recobs    import (RecognitionObserver, RecognitionHistory,
                                PlaybackHistory)
from .grammar.recobs_callbacks   import (CallbackRecognitionObserver,
                                         register_beginning_callback,
                                         register_recognition_callback,
                                         register_failure_callback,
                                         register_ending_callback,
                                         register_post_recognition_callback)

# --------------------------------------------------------------------------

from .actions           import (ActionBase, DynStrActionBase, ActionError,
                                Repeat, Key, Text, Mouse, Paste, Pause,
                                Mimic, Playback, WaitWindow, FocusWindow,
                                Function, StartApp, BringApp, PlaySound,
                                Typeable, Keyboard, typeables, RunCommand,
                                ContextAction)

if sys.platform.startswith("win"):
    from .actions       import (KeyboardInput, MouseInput, HardwareInput,
                                make_input_array, send_input_array)

# --------------------------------------------------------------------------

if sys.platform.startswith("win"):
    from .windows.clipboard import Clipboard
else:
    from .util              import Clipboard

# --------------------------------------------------------------------------

from .windows.rectangle import Rectangle, unit
from .windows.point     import Point
from .windows           import Window, Monitor, monitors

# --------------------------------------------------------------------------
from .language          import (Integer, IntegerRef, ShortIntegerRef,
                                Digits, DigitsRef,
                                Number, NumberRef)

# --------------------------------------------------------------------------
from .accessibility     import (CursorPosition, TextQuery,
                                get_accessibility_controller,
                                get_stopping_accessibility_controller)

from .rpc               import RPCServer, send_rpc_request
