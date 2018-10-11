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
Actions factory implementations
============================================================================

"""
from six import string_types

import dragonfly
from .loader import ActionFactoryBase
from .loader import ActionFactoryError as Error


#===========================================================================
# Actions factory classes.

class KeyActionFactory(ActionFactoryBase):

    name = "key"

    def build(self, call_info):
        spec = _get_single_anon_string(call_info.arguments, "Key action")
        return dragonfly.Key(spec)


#---------------------------------------------------------------------------

class TextActionFactory(ActionFactoryBase):

    name = "text"

    def build(self, call_info):
        spec = _get_single_anon_string(call_info.arguments, "Text action")
        return dragonfly.Text(spec)


#---------------------------------------------------------------------------
# Utility functions.

def _get_single_anon_string(arguments, description):
    if len(arguments) != 1:
        raise Error("%s expects 1 argument,"
                    " received %d." % (description, len(arguments)))
    argument = arguments[0]
    if argument.name is not None:
        raise Error("%s expects 1 argument"
                    " without a name." % description)
    if not isinstance(argument.value, string_types):
        raise Error("%s expects 1 argument"
                    " that is a literal string." % description)
    return argument.value
