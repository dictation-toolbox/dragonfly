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

import locale
from subprocess import Popen, PIPE

from six import string_types, binary_type

from .base_monitor import BaseMonitor
from .rectangle import Rectangle


#===========================================================================
# Monitor class for storing info about a single display monitor.

class X11Monitor(BaseMonitor):
    """
    The monitor class used on X11 (Linux).

    This implementation parses monitor information from
    ``xrandr``.
    """

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, name, rectangle):
        assert isinstance(name, string_types)
        self._name = name

        # Get a numeric value from the name that we can use as a handle.
        handle = hash(name)
        super(X11Monitor, self).__init__(handle, rectangle)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self._name)

    #-----------------------------------------------------------------------
    # Class methods to create new Monitor objects.

    @classmethod
    def get_all_monitors(cls):
        # pylint: disable=R0912,R0914,R0915
        # Suppress warnings about too many local variables.

        # Get updated monitor information from xrandr.
        try:
            p = Popen(["xrandr"], stdout=PIPE)
            stdout, _ = p.communicate()

            # Decode output if it is binary.
            encoding = locale.getpreferredencoding()
            if isinstance(stdout, binary_type):
                stdout = stdout.decode(encoding)

            # Handle non-zero return codes.
            if p.wait() > 0:
                print(stdout)
                raise RuntimeError("xrandr exited with non-zero return "
                                   "code %d" % p.returncode)
        except Exception as e:
            cls._log.error("Failed to execute command: %s. Is "
                           "xrandr installed?", e)
            raise e

        # Parse output from xrandr.
        monitors = []
        for line in stdout.split("\n")[1:]:  # skip the first line
            # Skip disconnected monitors, output modes and empty lines.
            if not line or "disconnected" in line or line.startswith("   "):
                continue

            # Get the information we need.
            parts = line.split()
            name = parts.pop(0)
            primary = "primary" in parts
            if primary:  # this monitor will be first in the list
                parts.remove("primary")

            # Find and remove info we don't need (e.g. 'connected' and
            # orientation info).
            i = 1
            for i, part in enumerate(parts):
                if "(" in part:  # e.g. '(normal'
                    break
            parts = parts[1:i]

            # Skip disabled monitors (no reported mode info).
            if not parts:
                continue

            # Get resolution and position info.
            res_info = parts[0].split("+")
            width, height = res_info.pop(0).split("x")
            origin_x, origin_y = res_info

            # Convert values to integers and create a rectangle object
            # representing the monitor's dimensions and relative position.
            width, height = int(width), int(height)
            origin_x, origin_y = int(origin_x), int(origin_y)
            dx = width - origin_x
            dy = height - origin_y
            rectangle = Rectangle(origin_x, origin_y, dx, dy)

            # Get a new or updated monitor object and add it to the list.
            monitor = cls.get_monitor(name, rectangle)
            if primary:
                monitors.insert(0, monitor)
            else:
                monitors.append(monitor)

        # Return the list of monitors.
        return monitors

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    def _set_name(self, name):
        assert isinstance(name, string_types)
        self._name = name

        # Also set the handle, as it is derived from the name.
        self._set_handle(hash(name))

    name = property(fget=lambda self: self._name,
                    fset=_set_name,
                    doc="Protected access to name attribute.")
