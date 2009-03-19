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
   class which based on the application context, i.e. foreground window
   executable, title, and handle


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


Class reference
----------------------------------------------------------------------------

"""

import copy
from dragonfly import get_log


#---------------------------------------------------------------------------

class Context(object):
    """
        Base class for other context classes.

        This base class implements some basic 
        infrastructure, including that's required for 
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

    _log = get_log("context.match")
    _log_match = _log

    #-----------------------------------------------------------------------
    # Initialization and aggregation methods.

    def __init__(self):
        self._str = ""

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._str)

    def copy(self):
        return copy_.deepcopy(self)

    #-----------------------------------------------------------------------
    # Logical operations.

    def __and__(self, other):
        return LogicAndContext(self, other)

    def __or__(self, other):
        return LogicOrContext(self, other)

    def __invert__(self):
        return LogicNotContext(self)

    #-----------------------------------------------------------------------
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
        return True


#---------------------------------------------------------------------------
# Wrapper contexts for combining contexts in logical structures.

class LogicAndContext(Context):

    def __init__(self, *children):
        self._children = children
        self._str = ", ".join(str(child) for child in children)

    def matches(self, executable, title, handle):
        for child in self._children:
            if not child.matches(executable, title, handle):
                return False
        return True


class LogicOrContext(Context):

    def __init__(self, *children):
        self._children = children
        self._str = ", ".join(str(child) for child in children)

    def matches(self, executable, title, handle):
        for child in self._children:
            if child.matches(executable, title, handle):
                return True
        return False


class LogicNotContext(Context):

    def __init__(self, child):
        self._child = child
        self._str = str(child)

    def matches(self, executable, title, handle):
        return not self._child.matches(executable, title, handle)


#---------------------------------------------------------------------------

class AppContext(Context):
    """
        Context class using foreground application details.

        This class determines whether the foreground window meets
        certain requirements.  Which requirements must be met for this
        context to match are determined by the constructor arguments.

        Constructor arguments:
         - *executable* (*str*) --
           (part of) the path name of the foreground application's
           executable; case insensitive
         - *title* (*str*) --
           (part of) the title of the foreground window; case insensitive

    """

    #-----------------------------------------------------------------------
    # Initialization methods.

    def __init__(self, executable=None, title=None, exclude=False):
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

        self._exclude = bool(exclude)

        self._str = "%s, %s, %s" % (self._executable, self._title,
                                    self._exclude)

    #-----------------------------------------------------------------------
    # Matching methods.

    def matches(self, executable, title, handle):
        executable = executable.lower()
        title = title.lower()

        if self._executable:
            found = (executable.find(self._executable) != -1)
            if self._exclude == found:
                self._log_match.debug("%s:"
                        " No match, executable doesn't match." % (self))
                return False
        if self._title:
            found = (title.find(self._title) != -1)
            if self._exclude == found:
                self._log_match.debug("%s:"
                        " No match, title doesn't match." % (self))
                return False

        if self._log_match: self._log_match.debug("%s: Match." % (self))
        return True
