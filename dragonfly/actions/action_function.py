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
Function action
============================================================================

"""

from inspect           import getargspec
from .action_base      import ActionBase, ActionError


#---------------------------------------------------------------------------

class Function(ActionBase):
    """
        Call a function with the recognized extras as keyword arguments.

    """

    def __init__(self, function):
        ActionBase.__init__(self)
        self._function = function
        self._str = function.__name__

        (args, varargs, varkw, defaults) = getargspec(self._function)
        if varkw:  self._filter_keywords = False
        else:      self._filter_keywords = True
        self._valid_keywords = set(args)

    def _execute(self, data=None):
        if not isinstance(data, dict):
            data = {}
        else:
            data = dict(data)

        if self._filter_keywords:
            invalid_keywords = set(data.keys()) - self._valid_keywords
            for key in invalid_keywords:
                del data[key]

        try:
            self._function(**data)
        except Exception, e:
            raise ActionError("%s: %s" % (self, e))
