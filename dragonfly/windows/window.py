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
import os

# Windows-specific
if sys.platform.startswith("win"):
    from .win32_window import Win32Window as Window

# Linux/X11
elif os.environ.get("XDG_SESSION_TYPE") == "x11":
    from .x11_window import X11Window as Window

# Mac OS
elif sys.platform == "darwin":
    from .darwin_window import DarwinWindow as Window

# Unsupported
else:
    from .fake_window import FakeWindow as Window
