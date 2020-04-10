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

from functools import reduce
from locale import getpreferredencoding
import logging

from six import PY2, integer_types, text_type


#---------------------------------------------------------------------------


class ActionError(Exception):
    pass


#---------------------------------------------------------------------------

class ActionBase(object):
    """
        Base class for Dragonfly's action classes.

    """

    _log_init = logging.getLogger("action.init")
    _log_exec = logging.getLogger("action.exec")
    _log = logging.getLogger("action")

    #-----------------------------------------------------------------------
    # Initialization and aggregation methods.

    def __init__(self):
        self._str = ""

    def __repr__(self):
        if PY2:
            return self.__unicode__().encode(getpreferredencoding())
        else:
            return self.__unicode__()

    def __unicode__(self):
        return u"%s(%s)" % (self.__class__.__name__, self._str)

    def __add__(self, other):
        return ActionSeries(self, other)

    def __iadd__(self, other):
        return ActionSeries(self, other)

    def __or__(self, other):
        return UnsafeActionSeries(self, other)

    def __ior__(self, other):
        return UnsafeActionSeries(self, other)

    def __mul__(self, factor):
        return ActionRepetition(self, factor)

    def __imul__(self, factor):
        return ActionRepetition(self, factor)

    #-----------------------------------------------------------------------
    # Execution methods.

    def bind(self, data=None):
        return BoundAction(self, data)

    def copy_bind(self, data=None):
        return BoundAction(self, data)

    def execute(self, data=None):
        self._log_exec.debug("Executing action: %s (%s)", self, data)
        try:
            if self._execute(data) is False:
                raise ActionError(str(self))
        except ActionError as e:
            self._log_exec.error("Execution failed: %s", e)
            return False
        except Exception as e:
            self._log_exec.exception("Execution of %s failed due to "
                                     "exception: %s", self, e)
            return False
        return True

    def _execute(self, data=None):
        """ Virtual method. """


#---------------------------------------------------------------------------

class DynStrActionBase(ActionBase):

    # pylint: disable=E1111,R1710
    # Suppress warnings about return statements in some methods.

    #-----------------------------------------------------------------------
    # Initialization methods.

    def __init__(self, spec=None, static=False):
        ActionBase.__init__(self)
        self.initialize(spec, static)

    def initialize(self, spec=None, static=False):
        self._spec = spec
        self._static = False
        self._events = None
        if spec is None: return

        if static or spec.find("%") == -1:
            self._static = True
            self._events = self._parse_spec(spec)
        else:
            self._static = False
            self._events = None

        self._str = "%r" % spec
        if not self._static:
            self._str += ", dynamic"

    def _parse_spec(self, spec):
        """ Virtual method. """

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

            if not data:
                spec = self._spec
            else:
                try:
                    spec = self._spec % data
                except KeyError:
                    self._log_exec.error("%s: Spec %r doesn't match data "
                                         "%r.", self, self._spec, data)
                    return False

            self._log_exec.debug("%s: Parsing dynamic spec: %r",
                                 self, spec)
            events = self._parse_spec(spec)
            self._execute_events(events)

    def _execute_events(self, events):
        """ Virtual method. """


#---------------------------------------------------------------------------

class BoundAction(ActionBase):

    #-----------------------------------------------------------------------
    # Initialization methods.

    def __init__(self, action, data):
        ActionBase.__init__(self)
        self._action = action
        self._data = data
        self._str = "%r, %r" % (action, data)

    #-----------------------------------------------------------------------
    # Execution methods.

    def execute(self, data=None):
        if not data:
            data = {}
        if self._data:
            data = dict(data)
            data.update(self._data)

        self._action.execute(data)


#---------------------------------------------------------------------------

class ActionSeries(ActionBase):

    #-----------------------------------------------------------------------
    # Initialization methods.

    #: Whether to stop executing if an action in the series fails.
    stop_on_failures = True

    def __init__(self, *actions):
        ActionBase.__init__(self)
        self._actions = list(actions)
        self._set_str()

    def _set_str(self):
        # Use a flat list of the series actions for a more readable
        # string representation.
        self._str = u", ".join(text_type(a)
                               for a in self.flat_action_list())

    def flat_action_list(self):
        # Get a flattened list of the series actions.
        result = []
        for action in self._actions:
            if isinstance(action, ActionSeries) and action.stop_on_failures:
                result.extend(action.flat_action_list())
            else:
                result.append(action)
        return result

    def append(self, other):
        assert isinstance(other, ActionBase)
        self._actions.append(other)
        self._set_str()

    def __iadd__(self, other):
        self.append(other)
        return self

    def __ior__(self, other):
        self.append(other)
        return self

    #-----------------------------------------------------------------------
    # Execution methods.

    def _execute(self, data=None):
        # Use a flat list of the series actions for more sensible sequence
        # termination and logging if an error occurs during execution.
        for action in self.flat_action_list():
            if action.execute(data) is False and self.stop_on_failures:
                return False
        return True

    def execute(self, data=None):
        # Override execute() to discard the return value.
        ActionBase.execute(self, data)

    def __str__(self):
        return reduce((lambda x, y: "{}+{}".format(x, y)), self._actions)


class UnsafeActionSeries(ActionSeries):
    stop_on_failures = False

    def execute(self, data=None):
        for action in self._actions:
            action.execute(data)

    def __str__(self):
        return reduce((lambda x, y: "{}|{}".format(x, y)), self._actions)


#---------------------------------------------------------------------------

class ActionRepetition(ActionBase):

    #-----------------------------------------------------------------------
    # Initialization methods.

    def __init__(self, action, factor):
        ActionBase.__init__(self)
        self._action = action
        self._factor = factor
        self._str = "%s, %s" % (action, factor)

        if not isinstance(factor, (int, Repeat)):
            raise TypeError("Invalid multiplier type: %r"
                            " (must be an int or a Repeat object)" % factor)

    #-----------------------------------------------------------------------
    # Execution methods.

    def execute(self, data=None):
        if isinstance(self._factor, integer_types):
            repeat = self._factor
        elif isinstance(self._factor, Repeat):
            repeat = self._factor.factor(data)
        else:
            raise ActionError("Invalid repeat factor: %r" % (self._factor,))

        for _ in range(repeat):
            if self._action.execute(data) is False:
                raise ActionError(str(self))

    def __str__(self):
        return '{{{}}}{}'.format(self._action, self._factor)


#---------------------------------------------------------------------------

class Repeat(object):
    # pylint: disable=line-too-long

    """
        Action repeat factor.

        Integer Repeat factors ignore any supply data::

            >>> integer = Repeat(count=3)
            >>> integer.factor()
            3
            >>> integer.factor({"foo": 4})  # Non-related data is ignored.
            3

        Integer Repeat factors can be specified with the ``*`` operator::

            >>> from dragonfly import Function
            >>> def func():
            ...     print("executing 'func'")
            ...
            >>> action = Function(func) * 3
            >>> action.execute()
            executing 'func'
            executing 'func'
            executing 'func'

        Named Repeat factors retrieved their factor-value from the
        supplied data::

            >>> named = Repeat("foo")
            >>> named.factor()
            Traceback (most recent call last):
              ...
            ActionError: No extra repeat factor found for name 'foo' ('NoneType' object is unsubscriptable)
            >>> named.factor({"foo": 4})
            4

        Repeat factors with both integer count and named extra values set
        combined (add) these together to determine their factor-value::

            >>> combined = Repeat(extra="foo", count=3)
            >>> combined.factor()
            Traceback (most recent call last):
              ...
            ActionError: No extra repeat factor found for name 'foo' ('NoneType' object is unsubscriptable)
            >>> combined.factor({"foo": 4}) # Combined factors 3 + 4 = 7.
            7

    """

    def __init__(self, extra=None, count=None):
        # Backward compatibility for swapped arguments
        # (#103)
        if isinstance(extra, integer_types):
            self._count = extra
            self._extra = count
        else:
            self._extra = extra
            self._count = count if count is not None else 0

    def factor(self, data=None):
        count = self._count
        if self._extra:
            try:
                additional = int(data[self._extra])
            except ValueError:
                raise ActionError("Repeat factor %r has invalid value %r"
                                  % (self._extra, data[self._extra]))
            except KeyError:
                raise ActionError("No extra repeat factor found for name %r"
                                  % (self._extra,))
            except Exception as e:
                raise ActionError("No extra repeat factor found for name %r"
                                  " (%s)" % (self._extra, e))
            count += additional
        return count

    def __str__(self):
        return '{}'.format(self._extra if self._extra else self._count)
