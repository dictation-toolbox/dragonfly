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

# The overridden methods in the Dragonfly.list.List class were
# automatically generated using the commented-out code immediately below.
#
#def construct_skeleton():
#   instance = list()
#   ignored_attributes = ('__class__', '__contains__', '__doc__',
#       '__eq__', '__ge__', '__getattribute__', '__getitem__',
#       '__getslice__', '__gt__', '__hash__', '__init__', '__iter__',
#       '__le__', '__len__', '__lt__', '__ne__', '__new__', '__repr__',
#       '__str__', 'count', 'index', '__delattr__', '__setattr__')
#   output = []
#   for name in dir(instance):
#       attribute = getattr(instance, name)
#       if not callable(attribute): continue
#       if name in ignored_attributes: continue
#       output.append("""\
#   def %(function)s(self, *args, **kwargs):
#       result = %(class)s.%(function)s(self, *args, **kwargs)
#       self._update(); return result
#""" % {"class": "list", "function": name})
#   return "".join(output)
#print construct_skeleton()
from six import string_types

#===========================================================================
# Base class for dragonfly list objects.

class ListBase(object):
    """ Base class for dragonfly list objects. """

    def __init__(self, name):
        self._name = name
        self._grammar = None
        self._batch_mode = False
        self._batch_updates = False

    #-----------------------------------------------------------------------
    # Protected attribute access.

    valid_types = property(
        lambda self: string_types,
        doc="The types of object at a Dragonfly list can contain.")

    name = property(lambda self: self._name,
                    doc="Read-only access to a list's name.")

    def _get_grammar(self):
        return self._grammar

    def _set_grammar(self, grammar):
        self._grammar = grammar
        # if self._grammar is None:
        #     self._grammar = grammar
        # else:
        #     raise TypeError("The grammar object a Dragonfly list is bound "
        #                     "to cannot be changed after it has been set.")

    grammar = property(_get_grammar, _set_grammar,
                       doc="Set-once access to a list's grammar object.")

    #-----------------------------------------------------------------------
    # Context manager methods for optimizing update_list() calls.

    def __enter__(self):
        self._batch_mode = True

    def __exit__(self, exc_type, exc_value, exc_tb):
        self._batch_mode = False
        if self._batch_updates:
            self._update()
            self._batch_updates = False

    #-----------------------------------------------------------------------
    # Notify the grammar of a list modification.

    def _update(self):
        """
        Internal method that notifies the engine of list updates.

        This method should be called internally by :class:`ListBase`sub-
        classes when the list is modified.
        """
        # Return early for batch mode. A single update_list() call will
        # occur in __exit__(), after a 'with' block.
        if self._batch_mode:
            self._batch_updates = True
            return

        # Validate list items.
        self._validate_items()

        # If this list is part of a grammar, then notify it of the list
        # changes.
        if self._grammar:
            self._grammar.update_list(self)

    def _validate_items(self):
        valid_types = self.valid_types
        invalid = [i for i in self if not isinstance(i, valid_types)]
        if invalid:
            raise TypeError("Dragonfly lists can only contain"
                            " string objects; received: %r" % invalid)

    #-----------------------------------------------------------------------
    # Accessor for the grammar to retrieve the list items.
    def get_list_items(self):
        raise NotImplementedError("Call to virtual method list_items()")


#===========================================================================
# Wrapper for Python's built-in list type.

class List(ListBase, list):
    """
        Wrapper for Python's built-in list that supports automatic
        engine notification of changes.

        Use :class:`~dragonfly.grammar.elements_basic.ListRef` elements
        in a grammar rule to allow matching speech to list items.
    """

    def __init__(self, name, *args, **kwargs):
        ListBase.__init__(self, name)
        list.__init__(self, *args, **kwargs)

    #-----------------------------------------------------------------------
    # Accessor for the grammar to retrieve the list items.

    def get_list_items(self):
        return self

    #-----------------------------------------------------------------------
    # Custom methods.

    def set(self, other):
        """Set the contents of this list to the contents of another."""
        with self:
            self[:] = other

    #-----------------------------------------------------------------------
    # Overridden list methods.

    def __add__(self, *args, **kwargs):
        result = list.__add__(self, *args, **kwargs)
        self._update(); return result
    def __delitem__(self, *args, **kwargs):
        result = list.__delitem__(self, *args, **kwargs)
        self._update(); return result
    def __delslice__(self, *args, **kwargs):
        # pylint: disable=no-member
        result = list.__delslice__(self, *args, **kwargs)
        self._update(); return result
    def __iadd__(self, *args, **kwargs):
        result = list.__iadd__(self, *args, **kwargs)
        self._update(); return result
    def __imul__(self, *args, **kwargs):
        result = list.__imul__(self, *args, **kwargs)
        self._update(); return result
    def __mul__(self, *args, **kwargs):
        result = list.__mul__(self, *args, **kwargs)
        self._update(); return result
    def __reduce__(self, *args, **kwargs):
        result = list.__reduce__(self, *args, **kwargs)
        self._update(); return result
    def __reduce_ex__(self, *args, **kwargs):
        result = list.__reduce_ex__(self, *args, **kwargs)
        self._update(); return result
    def __rmul__(self, *args, **kwargs):
        result = list.__rmul__(self, *args, **kwargs)
        self._update(); return result
    def __setitem__(self, *args, **kwargs):
        result = list.__setitem__(self, *args, **kwargs)
        self._update(); return result
    def __setslice__(self, *args, **kwargs):
        # pylint: disable=no-member
        result = list.__setslice__(self, *args, **kwargs)
        self._update(); return result
    def append(self, *args, **kwargs):
        result = list.append(self, *args, **kwargs)
        self._update(); return result
    def extend(self, *args, **kwargs):
        result = list.extend(self, *args, **kwargs)
        self._update(); return result
    def insert(self, *args, **kwargs):
        result = list.insert(self, *args, **kwargs)
        self._update(); return result
    def pop(self, *args, **kwargs):
        result = list.pop(self, *args, **kwargs)
        self._update(); return result
    def remove(self, *args, **kwargs):
        result = list.remove(self, *args, **kwargs)
        self._update(); return result
    def reverse(self, *args, **kwargs):
        result = list.reverse(self, *args, **kwargs)
        self._update(); return result
    def sort(self, *args, **kwargs):
        result = list.sort(self, *args, **kwargs)
        self._update(); return result
    def clear(self):
        del self[:]

#===========================================================================
# Wrapper for Python's built-in dict type.

class DictList(ListBase, dict):
    """
        Wrapper for Python's built-in dict that supports automatic
        engine notification of changes.  The object's keys are used
        as the elements of the engine list, while use of the associated
        values is left to the user.

        Use :class:`~dragonfly.grammar.elements_basic.DictListRef` elements
        in a grammar rule to allow matching speech to dictionary keys.
    """

    def __init__(self, name, *args, **kwargs):
        ListBase.__init__(self, name)
        dict.__init__(self, *args, **kwargs)

    #-----------------------------------------------------------------------
    # Accessor for the grammar to retrieve the list items.

    def get_list_items(self):
        return list(self.keys())

    #-----------------------------------------------------------------------
    # Custom methods.

    def set(self, other):
        """Set the contents of this dict to the contents of another."""
        with self:
            self.clear()
            self.update(other)

    #-----------------------------------------------------------------------
    # Overridden dict methods.

    def __delitem__(self, *args, **kwargs):
        result = dict.__delitem__(self, *args, **kwargs)
        self._update(); return result
    def __reduce__(self, *args, **kwargs):
        result = dict.__reduce__(self, *args, **kwargs)
        self._update(); return result
    def __reduce_ex__(self, *args, **kwargs):
        result = dict.__reduce_ex__(self, *args, **kwargs)
        self._update(); return result
    def __setitem__(self, *args, **kwargs):
        result = dict.__setitem__(self, *args, **kwargs)
        self._update(); return result
    def clear(self, *args, **kwargs):
        result = dict.clear(self, *args, **kwargs)
        self._update(); return result
    def fromkeys(self, *args, **kwargs):
        result = dict.fromkeys(self, *args, **kwargs)
        self._update(); return result
    def pop(self, *args, **kwargs):
        result = dict.pop(self, *args, **kwargs)
        self._update(); return result
    def popitem(self, *args, **kwargs):
        result = dict.popitem(self, *args, **kwargs)
        self._update(); return result
    def setdefault(self, *args, **kwargs):
        result = dict.setdefault(self, *args, **kwargs)
        self._update(); return result
    def update(self, *args, **kwargs):
        result = dict.update(self, *args, **kwargs)
        self._update(); return result
