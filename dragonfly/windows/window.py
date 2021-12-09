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
This module initializes the system window control and placement interface
for the current platform.
"""

import os
import sys


# Import the Window class for the current platform.
# Note: X11 is checked first here because it is possible to use on the other
#  supported platforms.
if os.environ.get("DISPLAY"):
    from dragonfly.windows.x11_window    import X11Window as Window

elif sys.platform.startswith("win"):
    from dragonfly.windows.win32_window  import Win32Window as Window

elif sys.platform == "darwin":
    from dragonfly.windows.darwin_window import DarwinWindow as Window

else:
    from dragonfly.windows.fake_window   import FakeWindow as Window
