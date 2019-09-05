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
Dictation container class for Natlink
============================================================================

This class is derived from :class:`DictationContainerBase` and implements
dictation formatting for the Natlink and Dragon NaturallySpeaking engine.

"""

from locale import getpreferredencoding

from six import text_type

from ..base import DictationContainerBase
from .dictation_format import WordFormatter


#---------------------------------------------------------------------------
# Natlink dictation class -- container for a series of dictated words.

class NatlinkDictationContainer(DictationContainerBase):
    """
        Container class for dictated words as recognized by the
        :class:`Dictation` element for the Natlink and DNS engine.

    """

    def __init__(self, words, methods):
        unicode_words = []
        for word in words:
            if isinstance(word, text_type):
                unicode_words.append(word)
            else:
                unicode_words.append(word.decode(getpreferredencoding()))
        DictationContainerBase.__init__(self, words=unicode_words,
                                        methods=methods)

    def format(self):
        """ Format and return this dictation. """
        formatter = WordFormatter()
        formatted = formatter.format_dictation(self._words)
        return self.apply_methods(formatted)
