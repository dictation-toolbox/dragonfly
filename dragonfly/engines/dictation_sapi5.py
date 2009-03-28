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
Dictation container for the SAPI5 engine.

"""

from ..log import get_log
from .dictation_base import DictationContainerBase


#---------------------------------------------------------------------------
# SAPI5 dictation class -- container for a series of dictated words.

class Sapi5DictationContainer(DictationContainerBase):

    def __init__(self, words):
        DictationContainerBase.__init__(self, words=words)

    def format(self):
        """ Format and return this dictation. """
        return " ".join(self._words)
