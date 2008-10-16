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
    This file implements the Context class for limiting under what
    circumstances of grammars and rules are active.
"""


try:
	import natlinkutils
except ImportError:
	natlinkutils = None

import copy
import dragonfly.log as log_


#---------------------------------------------------------------------------

class Context(object):

    _log_match = log_.get_log("context.match")

    #-----------------------------------------------------------------------
    # Initialization and aggregation methods.

    def __init__(self):
        self._str = ""
        self._following = []

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._str)

    def copy(self):
        return copy_.deepcopy(self)

    def append(self, other):
        assert isinstance(other, ActionBase)
        self._following.append(other)

    def __add__(self, other):
        copy = self.copy()
        copy.append(other)
        return copy

    def __iadd__(self, other):
        self.append(other)
        return self

    #-----------------------------------------------------------------------
    # Matching methods.

    def matches(self, executable, title, handle):
        return True


#---------------------------------------------------------------------------

class AppContext(Context):

    #-----------------------------------------------------------------------
    # Initialization methods.

    def __init__(self, executable=None, title=None):
        Context.__init__(self)

        if isinstance(executable, str):
            self._executable = executable.lower()
        elif executable is None:
            self._executable = None
        else:
            raise TypeError("executable argument must be a string or None;"
                        " received %r" % executable)

        if isinstance(title, str):
            self._title = title.lower()
        elif title is None:
            self._title = None
        else:
            raise TypeError("title argument must be a string or None;"
                        " received %r" % title)

        self._str = "%s, %s" % ( self._executable, self._title)

    #-----------------------------------------------------------------------
    # Matching methods.

    def matches(self, executable, title, handle):
        executable = executable.lower()
        title = title.lower()

        if self._executable and executable.find(self._executable) == -1:
            if self._log_match: self._log_match.debug("%s:"
                        " No match, executable doesn't match." % (self))
            return False
        if self._title and title.find(self._title) == -1:
            if self._log_match: self._log_match.debug("%s:"
                        " No match, title doesn't match." % (self))
            return False

        if self._log_match: self._log_match.debug("%s: Match." % (self))
        return True
