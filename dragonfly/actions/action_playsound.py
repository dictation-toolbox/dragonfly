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
PlaySound action
============================================================================

"""

import winsound
from .action_base         import ActionBase, ActionError


#---------------------------------------------------------------------------

class PlaySound(ActionBase):

    def __init__(self, name=None, file=None):
        ActionBase.__init__(self)
        if name is not None:
            self._name = name
            self._flags = winsound.SND_ASYNC | winsound.SND_ALIAS
        elif file is not None:
            self._name = file
            self._flags = winsound.SND_ASYNC | winsound.SND_FILENAME

        self._str = str(self._name)

    def _execute(self, data=None):
        winsound.PlaySound(self._name, self._flags)
