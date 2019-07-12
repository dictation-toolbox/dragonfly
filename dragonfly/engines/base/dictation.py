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
Dictation container base class
============================================================================

This class is used to store the recognized results of dictation elements
within voice-commands.  It offers access to both the raw spoken-form words
and be formatted written-form text.

The object can be expected to behave like a string,
responding as you would expect to string methods like :meth:`replace`.
The formatted text can be retrieved using
:meth:`~DictationContainerBase.format` or simply by  calling ``str(...)``
on a dictation container object.
By default, formatting returns the words joined with
spaces, but custom formatting can be applied by calling
string methods on the :class:`Dictation` object.
A tuple of the raw  spoken words can be
retrieved using :attr:`~DictationContainerBase.words`.

"""


#---------------------------------------------------------------------------
# Dictation base class -- base class for SR engine-specific containers
#  of dictated words.
import locale

from six import PY2


class DictationContainerBase(object):
    """
        Container class for dictated words as recognized by the
        :class:`Dictation` element.

        This base class implements the general functionality of dictation
        container classes.  Each supported engine should have a derived
        dictation container class which performs the actual engine-
        specific formatting of dictated text.

    """

    def __init__(self, words, methods=None):
        """
            A dictation container is created by passing it a sequence
            of words as recognized by the backend SR engine.
            Each word must be a Unicode string.

            :param words: A sequence of Unicode strings.
            :type words: sequence-of-unicode

            :param methods: Tuples describing string methods to call on the output.
            :type methods: list-of-triples

        """
        self._words = tuple(words)
        self._formatted = None
        self._methods = methods

    def __str__(self):
        if PY2:
            return self.__unicode__().encode(locale.getpreferredencoding())
        else:
            return self.__unicode__()

    def __unicode__(self):
        if self._formatted is None:
            self._formatted = self.format()
        return self._formatted

    def __repr__(self):
        message = u"%s(%s)" % (self.__class__.__name__,
                               u", ".join(self._words))
        if PY2:
            return message.encode(locale.getpreferredencoding())
        else:
            return message

    def __getattr__(self, name):
        return getattr(self.__str__(), name)

    def __add__(self, other):
        return self.__str__() + other

    def __radd__(self, other):
        return other + self.__str__()

    def __mul__(self, other):
        return self.__str__() * other

    def __rmul__(self, other):
        return self.__str__() * other

    def __getitem__(self, key):
        return self.__str__()[key]

    def __nonzero__(self):
        return bool(self.__str__())

    def __len__(self):
        return len(self.__str__())

    def __contains__(self, item):
        return item in self.__str__()

    @property
    def words(self):
        """ Sequence of the words forming this dictation. """
        return self._words

    def format(self):
        """ Format and return this dictation as a Unicode object. """
        return self.apply_methods(u" ".join(self._words))

    def apply_methods(self, joined_words):
        """
        Apply any string methods called on the :class:`Dictation` object to a given string. Called during :meth:`format`.
        """
        result = joined_words
        if result: # Do nothing for empty string
            for method in self._methods:
                if hasattr(result, method[0]):
                    result = getattr(result, method[0])(*method[1], **method[2])
                elif hasattr(self, method[0]):
                    result = getattr(self, method[0])(result, *method[1], **method[2])
                else:
                    raise AttributeError("'%s' is not a valid dictation or string method" % method[0])
        return result

    def apply(self, str_input, format_func):
        if callable(format_func):
            return format_func(str_input)
        else:
            raise TypeError("Argument passed to 'Dictation.apply' method must be callable, taking and returning a string.")

    def camel(self, str_input):
        def f(s):
            return s[0] + (s.title().replace(" ", "")[1:]
                    if len(s)>1 else "")
        return self.apply(str_input, f)
