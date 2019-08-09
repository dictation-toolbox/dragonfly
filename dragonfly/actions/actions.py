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

"""
This file offers access to various action classes.

"""
import sys

from .action_pause        import Pause
from .action_function     import Function
from .action_playback     import Playback
from .action_base         import (ActionBase, DynStrActionBase,
                                  Repeat, ActionError)
from .action_mimic        import Mimic
from .action_cmd          import RunCommand
from .action_context      import ContextAction
from .keyboard            import Keyboard, Typeable
from .action_key          import Key
from .action_text         import Text
from .action_paste        import Paste
from .action_waitwindow   import WaitWindow
from .action_focuswindow  import FocusWindow
from .action_startapp     import StartApp, BringApp

if sys.platform.startswith("win"):
    # Import Windows only classes and functions.
    from .action_mouse        import Mouse
    from .action_playsound    import PlaySound
else:
    # Import mocked classes and functions for other platforms.
    from ..os_dependent_mock import Mouse
    from ..os_dependent_mock import PlaySound
