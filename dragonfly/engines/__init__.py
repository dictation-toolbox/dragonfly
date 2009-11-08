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
Main SR engine back-end interface
============================================================================

"""

from ..log import get_log
from .base import EngineBase, EngineError, MimicFailure


#---------------------------------------------------------------------------

_default_engine = None
_engines_by_name = {}

def get_engine(name=None):
    global _default_engine, _engines_by_name

    log = get_log("engine")

    if name and name in _engines_by_name:
        # If the requested engine has already been loaded, return it.
        return _engines_by_name[name]
    elif not name and _default_engine:
        # If no specific engine is requested and an engine has already
        #  been loaded, return it.
        return _default_engine

    if not name or name == "natlink":
        # Attempt to retrieve the natlink back-end.
        try:
            from .backend_natlink import is_engine_available, get_engine
            if is_engine_available():
                _default_engine = get_engine()
                _engines_by_name["natlink"] = _default_engine
                return _default_engine
        except Exception, e:
            message = ("Exception while initializing natlink engine:"
                       " %s" % (e,))
            log.exception(message)
            if name:
                raise EngineError(message)

    if not name or name == "sapi5":
        # Attempt to retrieve the sapi5 back-end.
        try:
            from .backend_sapi5 import is_engine_available, get_engine
            if is_engine_available():
                _default_engine = get_engine()
                _engines_by_name["sapi5"] = _default_engine
                return _default_engine
        except Exception, e:
            message = ("Exception while initializing sapi5 engine:"
                       " %s" % (e,))
            log.exception(message)
            if name:
                raise EngineError(message)

    if not name:
        raise EngineError("No usable engines found.")
    else:
        raise EngineError("Requested engine %r not available." % (name,))
