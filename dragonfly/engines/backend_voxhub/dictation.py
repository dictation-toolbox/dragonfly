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
Dictation container class for the Sphinx engine
============================================================================

This class is used to store the recognized results of dictation elements 
within voice-commands.  It offers access to both the raw spoken-form words 
and be formatted written-form text.

The formatted text can be retrieved using
:meth:`~DictationContainerBase.format` or simply by  calling ``str(...)``
on a dictation container object. A tuple of the raw  spoken words can be
retrieved using :attr:`~DictationContainerBase.words`.

"""
from six import PY2

from ..base import DictationContainerBase


class VoxhubDictationContainer(DictationContainerBase):
    """
        Container class for dictated words as recognized by the
        :class:`Dictation` element.

    """

    def __init__(self, words):
        DictationContainerBase.__init__(self, words=words)

    def __repr__(self):
        message = u"%s(%s)" % (self.__class__.__name__,
                               u", ".join(self._words))
        if PY2:
            return message.encode()
        else:
            return message
