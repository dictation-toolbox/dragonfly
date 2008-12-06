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
    This file implements base classes for the action system.
"""


import copy as copy_
import dragonfly.log as log_


#---------------------------------------------------------------------------

class ActionError(Exception):
    pass


#---------------------------------------------------------------------------

class ActionBase(object):

    _log_init = log_.get_log("action.init")
    _log_exec = log_.get_log("action.exec")

    #-----------------------------------------------------------------------
    # Initialization and aggregation methods.

    def __init__(self):
        self._str = ""
        self._following = []

    def __str__(self):
        s = "%s(%s)" % (self.__class__.__name__, self._str)
        if self._following:
            s += "+".join([str(a) for a in self._following])
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

    #-----------------------------------------------------------------------
    # Execution methods.

    def evaluate(self, data=None):
        return self

    def execute(self, data=None):
        if self._log_exec:
            self._log_exec.debug("Executing action: %s" % self)
        self.evaluate(data)
        self._execute(data)
        [a.execute(data) for a in self._following]

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

    def bind_data(self, data):
        if not self._bound:
            self._bound = True
            self._bound_data = data

    def evaluate(self, data):
        if self._static or self._bound:
            return self
        else:
            clone = self.copy()
            clone.bind_data(data)
            return clone

    def _execute(self, data=None):
        if self._static:
            # If static, the events have already been parsed by the
            #  initialize() method.
            self._execute_events(self._events)

        else:
            # If not static, now is the time to build the dynamic spec,
            #  parse it, and execute the events.

            if self._bound:
                data = self._bound_data
            try:
                spec = self._spec % data
            except KeyError:
                if self._log_exec: self._log_exec.error("%s:"
                                    " Spec %r doesn't match data %s."
                                    % (self, self._spec, data))
                return False

            if self._log_exec: self._log_exec.debug("%s:"
                                " Parsing dynamic spec: %r" % (self, spec))
            events = self._parse_spec(spec)
            self._execute_events(events)

    def _execute_events(self, events):
        pass

