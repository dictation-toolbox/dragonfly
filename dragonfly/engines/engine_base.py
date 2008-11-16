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
    This file implements the engine base class.
"""


import dragonfly.log as log_


#---------------------------------------------------------------------------

class EngineBase(object):

    _log = log_.get_log("engine")

    @classmethod
    def is_available(cls):
        return False

    #-----------------------------------------------------------------------

    def __str__(self):
        return "%s()" % self.__class__.__name__

    #-----------------------------------------------------------------------
    # Methods for working with grammars.

    def load_grammar(self, grammar, *args, **kwargs):
        raise NotImplementedError("Engine %s not implemented." % self)

    def update_list(self, lst, grammar):
        raise NotImplementedError("Engine %s not implemented." % self)
