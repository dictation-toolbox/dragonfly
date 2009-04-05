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

The formatted text can be retrieved using :meth:`.format` or simply by 
calling ``str(...)`` on a dictation container object. A tuple of the raw 
spoken words can be retrieved using :meth:`.words`.

"""


#---------------------------------------------------------------------------
# Dictation base class -- base class for SR engine-specific containers
#  of dictated words.

class DictationContainerBase(object):
    """
        Container class for dictated words as recognized by the
        :class:`Dictation` element.

        This base class implements the general functionality of dictation 
        container classes.  Each supported engine should have a derived 
        dictation container class which performs the actual engine-
        specific formatting of dictated text.

    """

    def __init__(self, words):
        self._words = tuple(words)
        self._formatted = None

    def __str__(self):
        if self._formatted is None:
            self._formatted = self.format()
        return self._formatted

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ", ".join(self._words))

    @property
    def words(self):
        """ Sequence of the words forming this dictation. """
        return self._words

    def format(self):
        """ Format and return this dictation. """
        return " ".join(self._words)
