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
This module initializes the correct keyboard interface for the current
platform.
"""

import os
import sys

# TODO Implement classes for Wayland (XDG_SESSION_TYPE == "wayland").

# Import the Keyboard, KeySymbols and Typeable classes for the current
# platform. Always use the base classes for building documentation.
doc_build = bool(os.environ.get("SPHINX_BUILD_RUNNING"))
if sys.platform.startswith("win") and not doc_build:
    # Import classes for Windows.
    from ._win32 import Keyboard, Typeable, Win32KeySymbols as KeySymbols

elif sys.platform == "darwin" and not doc_build:
    # Import classes for Mac OS.
    from ._pynput import Keyboard, Typeable, DarwinKeySymbols as KeySymbols

elif os.environ.get("XDG_SESSION_TYPE") == "x11" and not doc_build:
    # Import classes for X11 (typically used on Linux systems).
    # The XDG_SESSION_TYPE environment variable may not be set in some
    # circumstances, in which case it can be set manually in ~/.profile.
    from ._x11_base import Typeable, XdoKeySymbols as KeySymbols

    # Import the keyboard for typing through xdotool.
    from ._x11_xdotool import XdotoolKeyboard as Keyboard

    # libxdo does work and is a bit faster, but doesn't work with Python 3.
    # Unfortunately python-libxdo also hasn't been updated recently.
    # from ._x11_libxdo import LibxdoKeyboard as Keyboard

else:
    # No keyboard implementation is available. Dragonfly can function
    # without a keyboard class, so don't raise an error or log any
    # messages. Errors/messages will occur later if the keyboard is used.
    from ._base import (BaseKeyboard as Keyboard, Typeable,
                        MockKeySymbols as KeySymbols)

# Initialize a Keyboard instance.
keyboard = Keyboard()
