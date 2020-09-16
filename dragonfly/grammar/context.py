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
Context classes
============================================================================

Dragonfly uses context classes to define when grammars and
rules should be active.  A context is an object with a
:meth:`Context.matches` method which returns *True* if the
system is currently within that context, and *False* if it
is not.

The following context classes are available:

 - :class:`Context` --
   the base class from which all other context classes are derived
 - :class:`AppContext` --
   class which is based on the application context, i.e. foreground
   window executable, title, and handle
 - :class:`FuncContext` --
   class that evaluates a given function/lambda/callable, whose return
   value is interpreted as a *bool*, determining whether the context is
   active


Logical operations
----------------------------------------------------------------------------

It is possible to modify and combine the behavior of contexts using the
Python's standard logical operators:

:logical AND: ``context1 & context2`` -- *all* contexts must match
:logical OR: ``context1 | context2`` --
   *one or more* of the contexts must match
:logical NOT: ``~context1`` -- *inversion* of when the context matches

For example, to create a context which will match when
Firefox is in the foreground, but only if Google Reader is
*not* being viewed::

   firefox_context = AppContext(executable="firefox")
   reader_context = AppContext(executable="firefox", title="Google Reader")
   firefox_but_not_reader_context = firefox_context & ~reader_context


Matching other window attributes
----------------------------------------------------------------------------

The :class:`AppContext` class can be used to match window attributes and
properties other than the title and executable. To do this, pass extra
keyword arguments to the constructor::

   # Context for a maximized Firefox window.
   maximized_firefox = AppContext(executable="firefox", is_maximized=True)

   # Context for a browser in fullscreen mode.
   # 'role' and 'is_fullscreen' are X11 only.
   fullscreen_browser = AppContext(role="browser", is_fullscreen=True)

   # Context for Android Studio or PyCharm using the X11 'cls' property.
   AppContext(cls=["jetbrains-studio", "jetbrains-pycharm-ce"])



Class reference
----------------------------------------------------------------------------

"""

import copy
import inspect
import logging


# --------------------------------------------------------------------------
from six import string_types


class Context(object):
    """
        Base class for other context classes.

        This base class implements some basic
        infrastructure, including what's required for
        logical operations on context objects.  Derived
        classes should at least do the following things:

         - During initialization, set *self._str* to some descriptive,
           human readable value.  This attribute is used by the
           ``__str__()`` method.
         - Overload the :meth:`Context.matches` method to implement
           the logic to determine when to be active.

        The *self._log* logger objects should be used in methods of
        derived classes for logging purposes.  It is a standard logger
        object from the *logger* module in the Python standard library.

    """

    _log = logging.getLogger("context.match")
    _log_match = _log

    # ----------------------------------------------------------------------
    # Initialization and aggregation methods.

    def __init__(self):
        self._str = ""

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self._str)

    def copy(self):
        return copy.deepcopy(self)

    # ----------------------------------------------------------------------
    # Logical operations.

    def __and__(self, other):
        return LogicAndContext(self, other)

    def __or__(self, other):
        return LogicOrContext(self, other)

    def __invert__(self):
        return LogicNotContext(self)

    # ----------------------------------------------------------------------
    # Matching methods.

    def matches(self, executable, title, handle):
        """
            Indicate whether the system is currently within this context.

            Arguments:
             - *executable* (*str*) --
               path name to the executable of the foreground application
             - *title* (*str*) -- title of the foreground window
             - *handle* (*int*) -- window handle to the foreground window

            The default implementation of this method simply returns *True*.

            .. note::

               This is generally the method which developers should
               overload to give derived context classes custom
               functionality.

        """
        # pylint: disable=unused-argument,no-self-use
        return True


# --------------------------------------------------------------------------
# Wrapper contexts for combining contexts in logical structures.

class LogicAndContext(Context):

    def __init__(self, *children):
        Context.__init__(self)
        self._children = children
        self._str = ", ".join(str(child) for child in children)

    def matches(self, executable, title, handle):
        for child in self._children:
            if not child.matches(executable, title, handle):
                return False
        return True


class LogicOrContext(Context):

    def __init__(self, *children):
        Context.__init__(self)
        self._children = children
        self._str = ", ".join(str(child) for child in children)

    def matches(self, executable, title, handle):
        for child in self._children:
            if child.matches(executable, title, handle):
                return True
        return False


class LogicNotContext(Context):

    def __init__(self, child):
        Context.__init__(self)
        self._child = child
        self._str = str(child)

    def matches(self, executable, title, handle):
        return not self._child.matches(executable, title, handle)


# --------------------------------------------------------------------------

class AppContext(Context):
    """
        Context class using foreground application details.

        This class determines whether the foreground window meets
        certain requirements.  Which requirements must be met for this
        context to match are determined by the constructor arguments.

        If multiple strings are passed in a list, True will be returned if
        the foreground window matches one or more of them. This applies to
        the *executable* and *title* arguments and key word arguments for
        most window attributes.

        Constructor arguments:
         - *executable* (*str* or *list*) --
           (part of) the path name of the foreground application's
           executable; case insensitive
         - *title* (*str* or *list*) --
           (part of) the title of the foreground window; case insensitive
         - *key word arguments* --
           optional window attributes/properties and expected values;
           case insensitive

    """

    # ----------------------------------------------------------------------
    # Initialization methods.

    def __init__(self, executable=None, title=None, exclude=False,
                 **kwargs):
        # pylint: disable=too-many-branches
        # Suppress warnings about too many if-else branches.
        Context.__init__(self)

        # Allow Unicode or strings to be used for executables and titles.
        if isinstance(executable, string_types):
            self._executable = [executable.lower()]
        elif isinstance(executable, (list, tuple)):
            self._executable = [e.lower() for e in executable]
        elif executable is None:
            self._executable = None
        else:
            raise TypeError("executable argument must be a string or None;"
                            " received %r" % executable)

        if isinstance(title, string_types):
            self._title = [title.lower()]
        elif isinstance(title, (list, tuple)):
            self._title = [t.lower() for t in title]
        elif title is None:
            self._title = None
        else:
            raise TypeError("title argument must be a string or None;"
                            " received %r" % title)

        # Handle keyword arguments.
        new_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, string_types):
                values = [value.lower()]
            elif isinstance(value, list):
                values = [str(v).lower() for v in value]
            elif value is None:
                values = None
            else:
                values = [value]
            new_kwargs[key] = values

        self._exclude = bool(exclude)
        self._str = "%s, %s, %s" % (self._executable, self._title,
                                    self._exclude)
        self._kwargs = new_kwargs
        if self._kwargs:
            self._str += ", %s" % self._kwargs

    # ----------------------------------------------------------------------
    # Matching methods.

    def matches(self, executable, title, handle):
        # pylint: disable=too-many-branches
        # Suppress warnings about too many if-else branches.
        if isinstance(executable, string_types):
            executable = executable.lower()
        if isinstance(title, string_types):
            title = title.lower()

        if self._executable:
            found = False
            if isinstance(executable, string_types):
                for match in self._executable:
                    if executable.find(match) != -1:
                        found = True
                        break
            if self._exclude == found:
                self._log_match.debug("%s: No match, executable doesn't "
                                      "match.", self)
                return False

        if self._title:
            found = False
            if isinstance(title, string_types):
                for match in self._title:
                    if title.find(match) != -1:
                        found = True
                        break
            if self._exclude == found:
                self._log_match.debug("%s: No match, title doesn't match.",
                                      self)
                return False

        if self._kwargs:
            # Import locally to avoid import cycles.
            from dragonfly.windows import Window
            window = Window.get_window(handle)

            found = False
            for attr, expected_values in self._kwargs.items():
                try:
                    # Get the window attribute.
                    attr_value = getattr(window, attr)
                except AttributeError:
                    self._log_match.warning("%s: Skipped missing window"
                                            " attribute '%s'",
                                            self, attr)
                    continue

                # Check if the window attribute matched.
                for match in expected_values:
                    is_string = isinstance(attr_value, string_types)
                    found = (
                        not is_string and match == attr_value or
                        is_string and attr_value.lower().find(match) != -1
                    )
                    if found:
                        break

            if self._exclude == found:
                self._log_match.debug("%s: No match, not all extra"
                                      " attributes match.", self)
                return False

        if self._log_match:
            self._log_match.debug("%s: Match.", self)
        return True


# --------------------------------------------------------------------------

class FuncContext(Context):
    """
        Context class that evaluates a given function, whose return
        value is interpreted as a *bool*, determining whether the
        context is active.

        The foreground application details are optionally passed to the
        function as arguments named *executable*, *title*, and/or
        *handle*, if any/each matches a so-named keyword argument of the
        function. Default arguments may also be passed to the function,
        through this class's constructor.

    """

    def __init__(self, function, **defaults):
        """
            Constructor arguments:
             - *function* (callable) --
               the function to call when this context is evaluated
             - defaults --
               optional default keyword-values for the arguments with
               which the function will be called

        """

        Context.__init__(self)
        self._function = function
        self._defaults = defaults
        self._str = "%s, defaults: %s" % (self._function, self._defaults)

        (args, _, varkw, defaults) = inspect.getargspec(self._function)
        if varkw:  self._filter_keywords = False
        else:      self._filter_keywords = True
        self._valid_keywords = set(args)

    def matches(self, executable, title, handle):
        arguments = dict(self._defaults)
        arguments.update(executable=executable, title=title, handle=handle)

        if self._filter_keywords:
            invalid_keywords = set(arguments.keys()) - self._valid_keywords
            for key in invalid_keywords:
                del arguments[key]

        try:
            match = bool(self._function(**arguments))
            if match:
                self._log_match.debug("%s: Match.", self)
            else:
                self._log_match.debug("%s: No match, function"
                                      " returned false.", self)
            return match
        except:
            self._log.exception("Exception from function %s:",
                                self._function.__name__)
            # Fallback to matching
            return True
