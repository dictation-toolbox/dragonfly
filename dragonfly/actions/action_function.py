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

The :class:`Function` action wraps a callable, optionally with some 
default keyword argument values.  On execution, the execution data 
(commonly containing the recognition extras) are combined with the 
default argument values (if present) to form the arguments with which 
the callable will be called.

Simple usage::

    >>> def func(count):
    ...     print "count:", count
    ...
    >>> action = Function(func)
    >>> action.execute({"count": 2})
    count: 2
    >>> action.execute({"count": 2, "flavor": "vanilla"})
    count: 2          # Additional keyword arguments are ignored.

Usage with default arguments::

    >>> def func(count, flavor):
    ...     print "count:", count
    ...     print "flavor:", flavor
    ...
    >>> action = Function(func, flavor="spearmint")
    >>> action.execute({"count": 2})
    count: 2
    flavor: spearmint
    >>> action.execute({"count": 2, "flavor": "vanilla"})
    count: 2
    flavor: vanilla


Class reference
----------------------------------------------------------------------------

"""

from inspect           import getargspec
from .action_base      import ActionBase, ActionError


#---------------------------------------------------------------------------

class Function(ActionBase):
    """ Call a function with extra keyword arguments. """

    def __init__(self, function, **defaults):
        """
            Constructor arguments:
             - *function* (callable) --
               the function to call when this action is executed
             - defaults --
               default keyword-values for the arguments with which
               the function will be called

        """
        ActionBase.__init__(self)
        self._function = function
        self._defaults = defaults
        self._str = function.__name__

        (args, varargs, varkw, defaults) = getargspec(self._function)
        if varkw:  self._filter_keywords = False
        else:      self._filter_keywords = True
        self._valid_keywords = set(args)

    def _execute(self, data=None):
        arguments = dict(self._defaults)
        if isinstance(data, dict):
            arguments.update(data)

        if self._filter_keywords:
            invalid_keywords = set(arguments.keys()) - self._valid_keywords
            for key in invalid_keywords:
                del arguments[key]

        try:
            self._function(**arguments)
        except Exception, e:
            self._log.exception("Exception from function %s:"
                                % self._function.__name__)
            raise ActionError("%s: %s" % (self, e))
