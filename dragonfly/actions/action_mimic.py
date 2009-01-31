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
Mimic action -- mimic a recognition
============================================================================

"""


import win32con
from dragonfly.actions.action_base  import ActionBase, ActionError
from dragonfly.engines.engine       import get_engine


#---------------------------------------------------------------------------

class Mimic(ActionBase):
    """
        Mimic recognition action.

        The constructor arguments are the words which will be 
        mimicked.  These should be passed as a variable argument 
        list.  For example: ::

            action = Mimic("hello", "world", r"!\\exclamation-mark")
            action.execute()

        If an error occurs during mimicking the given 
        recognition, then an *ActionError* is raised.  A common 
        error is that the engine does not know the given words 
        and can therefore not recognize them.  For example, the 
        following attempts to mimic recognition of *one single 
        word* including a space and an exclamation-mark; this 
        will almost certainly fail: ::

            Mimic("hello world!").execute()   # Will raise ActionError.

    """

    def __init__(self, *words):
        self.words = list(words)
        ActionBase.__init__(self)

    def _execute(self, data=None):
        engine = get_engine()
        self._log.debug("Mimicking recognition: %r" % self.words)
        try:
            engine.mimic(self.words)
        except Exception, e:
            self._log.warning("Mimicking failed: %s" % e)
            raise ActionError("Mimicking failed: %s" % e)
