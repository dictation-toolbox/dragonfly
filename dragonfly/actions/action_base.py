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
ActionBase base class
============================================================================

"""


import copy as copy_
from ..log import get_log


#---------------------------------------------------------------------------

class ActionError(Exception):
    pass


#---------------------------------------------------------------------------

class ActionBase(object):
    """
        Base class for Dragonfly's action classes.

    """

    _log_init = get_log("action.init")
    _log_exec = get_log("action.exec")
    _log = get_log("action")

    #-----------------------------------------------------------------------
    # Initialization and aggregation methods.

    def __init__(self):
        self._str = ""
        self._following = []
        self._data = None
        self._bound = False
        self._repeat_factors = []

    def __str__(self):
        s = "%s(%s)" % (self.__class__.__name__, self._str)
        if self._following:
            actions = [s] + [str(a) for a in self._following]
            s = " + ".join(actions)
        if self._repeat_factors:
            if self._following:
                s = "(" + s + ")"
            s = "%s * (%s)" % (s, self._repeat_factors)
        if self._bound and self._data:
            if self._following and not self._repeat_factors:
                s = "(" + s + ")"
            s = "%s %% %r" % (s, self._data)
        return s

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

    def __mul__(self, other):
        copy = self.copy()
        copy *= other
        return copy

    def __imul__(self, other):
        if not isinstance(other, (int, Repeat)):
            raise TypeError("Invalid multiplier type: %r"
                            " (must be an int or a Repeat object)" % other)
        self._repeat_factors.append(other)
        return self

    #-----------------------------------------------------------------------
    # Execution methods.

    def copy_bind(self, data=None):
        if self._bound:
            return self
        else:
            action = self.copy()
            action._data = data
            action._bound = True
            return action

    def execute(self, data=None):
        if self._bound:
            data = self._data
        self._log_exec.debug("Executing action: %s" % self.copy_bind(data))
        try:
            repeat = 1
            for factor in self._repeat_factors:
                if isinstance(factor, int):
                    repeat *= factor
                elif isinstance(factor, Repeat):
                    repeat *= factor.factor(data)
            for index in range(repeat):
                if self._execute(data) == False:
                    raise ActionError(str(self))
                for a in self._following:
                    if a.execute(data) == False:
                        raise ActionError(str(a))
        except ActionError, e:
            self._log_exec.error("Execution failed: %s" % e)
            return False

    def _execute(self, data=None):
        pass


#---------------------------------------------------------------------------

class DynStrActionBase(ActionBase):

    #-----------------------------------------------------------------------
    # Initialization methods.

    def __init__(self, spec=None, static=False):
        ActionBase.__init__(self)
        self.initialize(spec, static)

    def initialize(self, spec=None, static=False):
        self._spec = spec
        self._static = False
        self._events = None
        self._bound = False
        self._bound_data = None
        if spec is None: return

        if static or spec.find("%") == -1:
            self._static = True
            self._events = self._parse_spec(spec)
        else:
            self._static = False
            self._events = None

        self._str = "%r" % spec
        if not self._static: self._str += ", dynamic"

    def _parse_spec(self, spec):
        pass

    #-----------------------------------------------------------------------
    # Execution methods.

    def _execute(self, data=None):
        if self._static:
            # If static, the events have already been parsed by the
            #  initialize() method.
            self._execute_events(self._events)

        else:
            # If not static, now is the time to build the dynamic spec,
            #  parse it, and execute the events.

            if data is None:
                data = {}
            try:
                spec = self._spec % data
            except KeyError:
                if self._log_exec: self._log_exec.error("%s:"
                                    " Spec %r doesn't match data %r."
                                    % (self, self._spec, data))
                return False

            if self._log_exec: self._log_exec.debug("%s:"
                                " Parsing dynamic spec: %r" % (self, spec))
            events = self._parse_spec(spec)
            self._execute_events(events)

    def _execute_events(self, events):
        pass


#---------------------------------------------------------------------------

class Repeat(object):

    def __init__(self, count=None, extra=None):
        if count is not None:  self._count = count
        else:                  self._count = 0
        self._extra = extra

    def factor(self, data):
        count = self._count
        if self._extra:
            try:
                additional = data[self._extra]
            except KeyError:
                raise ActionError("No extra repeat factor found for name %r"
                                  % self._extra)
            count += additional
        return count
