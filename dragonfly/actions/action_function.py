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
    ...     print("count: %d" % count)
    ...
    >>> action = Function(func)
    >>> action.execute({"count": 2})
    count: 2
    True
    >>> # Additional keyword arguments are ignored:
    >>> action.execute({"count": 2, "flavor": "vanilla"})
    count: 2
    True

Usage with default arguments::

    >>> def func(count, flavor):
    ...     print("count: %d" % count)
    ...     print("flavor: %s" % flavor)
    ...
    >>> # The Function object can be given default argument values:
    >>> action = Function(func, flavor="spearmint")
    >>> action.execute({"count": 2})
    count: 2
    flavor: spearmint
    True
    >>> # Arguments given at the execution-time to override default values:
    >>> action.execute({"count": 2, "flavor": "vanilla"})
    count: 2
    flavor: vanilla
    True

Usage with the ``remap_data`` argument::

    >>> def func(x, y, z):
    ...     print("x: %d" % x)
    ...     print("y: %d" % y)
    ...     print("z: %d" % z)
    ...
    >>> # The Function object can optionally be given a second dictionary
    >>> # argument to use extras with different names. It should be
    >>> # compatible with the 'defaults' parameter:
    >>> action = Function(func, dict(n="x", m="y"), z=4)
    >>> action.execute({"n": 2, "m": 3})
    x: 2
    y: 3
    z: 4
    True


Class reference
----------------------------------------------------------------------------

"""

import inspect

import six

from dragonfly.actions.action_base      import ActionBase, ActionError


#---------------------------------------------------------------------------

class Function(ActionBase):
    """ Call a function with extra keyword arguments. """

    def __init__(self, function, remap_data=None, **defaults):
        """
            Constructor arguments:
             - *function* (callable) --
               the function to call when this action is executed
             - *remap_data* (dict, default: None) --
               optional dict of data keys to function keyword arguments
             - defaults --
               default keyword-values for the arguments with which
               the function will be called

        """
        ActionBase.__init__(self)
        self._function = function
        self._defaults = defaults
        self._remap_data = remap_data or {}
        self._str = function.__name__

        # Get argument names and defaults. Use getfullargspec() in Python 3
        # to avoid deprecation warnings.
        if six.PY2:
            # pylint: disable=deprecated-method
            argspec = inspect.getargspec(self._function)
        else:
            argspec = inspect.getfullargspec(self._function)

        args, varkw = argspec[0], argspec[2]
        self._filter_keywords = not varkw
        self._valid_keywords = set(args)

    def _execute(self, data=None):
        arguments = dict(self._defaults)
        if isinstance(data, dict):
            arguments.update(data)

        # Remap specified names.
        if arguments and self._remap_data:
            for old_name, new_name in self._remap_data.items():
                if old_name in data:
                    arguments[new_name] = arguments.pop(old_name)

        if self._filter_keywords:
            invalid_keywords = set(arguments.keys()) - self._valid_keywords
            for key in invalid_keywords:
                del arguments[key]

        try:
            self._function(**arguments)
        except Exception as e:
            self._log.exception("Exception from function %s:",
                                self._function.__name__)
            raise ActionError("%s: %s" % (self, e))

    def __str__(self):
        if (self._str == '<lambda>'):
            try:
                return '{!r}()'.format(inspect.getsource(self._function)
                                       .strip())
            except (OSError, IOError):
                pass
        return '{!r}()'.format(self._str)
