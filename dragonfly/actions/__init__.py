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

# Import OS-agnostic classes
from .action_pause        import Pause
from .action_function     import Function
from .action_playback     import Playback
from .action_base         import (ActionBase, DynStrActionBase,
                                  Repeat, ActionError)
from .action_mimic        import Mimic

# Import Windows OS dependent classes only for Windows
if sys.platform.startswith("win"):
    from .action_key          import Key
    from .action_text         import Text
    from .action_mouse        import Mouse
    from .action_paste        import Paste
    from .action_waitwindow   import WaitWindow
    from .action_focuswindow  import FocusWindow
    from .action_startapp     import StartApp, BringApp
    from .action_playsound    import PlaySound
    from .keyboard import Typeable, Keyboard
    from .typeables import typeables
    from .sendinput import (KeyboardInput, MouseInput, HardwareInput,
                            make_input_array, send_input_array)
else:
    from ..os_dependent_mock import Key
    from ..os_dependent_mock import Text
    from ..os_dependent_mock import Mouse
    from ..os_dependent_mock import Paste
    from ..os_dependent_mock import WaitWindow
    from ..os_dependent_mock import FocusWindow
    from ..os_dependent_mock import StartApp, BringApp
    from ..os_dependent_mock import PlaySound
    from ..os_dependent_mock import (Typeable, Keyboard, typeables, KeyboardInput,
                                     MouseInput, HardwareInput, make_input_array,
                                     send_input_array)
