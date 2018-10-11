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
Context factory implementations
============================================================================

"""
from six import string_types

import dragonfly
from .loader    import ContextFactoryBase
from .loader    import ContextFactoryError as Error


#===========================================================================
# Context factory classes.

class GlobalContextFactory(ContextFactoryBase):

    name = "global"

    def build(self, call_info):
        if call_info.arguments:
            raise Error("Global context doesn't need arguments;"
                        " received: %r" % (call_info.arguments,))
        return dragonfly.Context()


#---------------------------------------------------------------------------

class ExecutableContextFactory(ContextFactoryBase):

    name = "executable"

    def build(self, call_info):
        executable = _get_single_anon_string(call_info.arguments,
                                             "Executable context")
        return dragonfly.AppContext(executable=executable)


#---------------------------------------------------------------------------

class TitleContextFactory(ContextFactoryBase):

    name = "title"

    def build(self, call_info):
        title = _get_single_anon_string(call_info.arguments,
                                        "Title context")
        return dragonfly.AppContext(title=title)


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
