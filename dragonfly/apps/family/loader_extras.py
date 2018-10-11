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
Extras factory implementations
============================================================================

"""

import dragonfly
from .loader    import ExtrasFactoryBase, ExtrasFactoryError


#===========================================================================
# Extras factory classes.

class DictationExtrasFactory(ExtrasFactoryBase):

    name = "dictation"

    def build(self, call_info):
        name = call_info.name
        if call_info.arguments:
            raise SyntaxError("Invalid arguments for dictation extra: %r"
                              % (call_info.arguments,))
        return dragonfly.Dictation(name)


#---------------------------------------------------------------------------

class IntegerExtrasFactory(ExtrasFactoryBase):

    name = "integer"

    def build(self, call_info):
        name = call_info.name
        arguments = call_info.arguments
        # Check argument input here.
        min = arguments.pop().value
        max = arguments.pop().value
        if arguments:
            raise SyntaxError("Invalid arguments for integer extra: %r"
                              % (arguments,))
        return dragonfly.Integer(name=name, min=min, max=max)
