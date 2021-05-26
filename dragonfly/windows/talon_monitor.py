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

# pylint: disable=E0401
from talon import ui

from .base_monitor import BaseMonitor
from .rectangle import Rectangle


#===========================================================================
# Monitor class for storing info about a single display monitor.

class TalonMonitor(BaseMonitor):
    """
    The monitor class used under Talon.
    """

    @classmethod
    def get_all_monitors(cls):
        monitors = []
        for screen in ui.screens():
            rectangle = Rectangle(screen.x, screen.y, screen.width, screen.height)
            monitors.append(cls.get_monitor(id(screen), rectangle))
        return monitors

    @property
    def name(self):
        """ The name of this monitor. """
        return self.handle.name
