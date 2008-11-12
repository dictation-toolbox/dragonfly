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
    This file implements an interface to the available engines.
"""


#---------------------------------------------------------------------------

def get_engine():
    if _engine:
        return _engine

    engine = get_natlink_engine()
    if engine:
        return engine

    engine = get_sapi5_engine()
    if engine:
        return engine

    raise Exception

_engine = None


#---------------------------------------------------------------------------

NatlinkEngine = None
_natlink_engine = None

def get_natlink_engine():
    global NatlinkEngine
    global _natlink_engine, _engine

    if _natlink_engine:
        return _natlink_engine

    import dragonfly.engines.engine_natlink as engine_natlink
    NatlinkEngine = engine_natlink.NatlinkEngine

    if NatlinkEngine.is_available():
        _natlink_engine = NatlinkEngine()
        _engine = _natlink_engine
        return _natlink_engine
    return None


#---------------------------------------------------------------------------

Sapi5Engine = None
_sapi5_engine = None

def get_sapi5_engine():
    global Sapi5Engine
    global _sapi5_engine, _engine

    if _sapi5_engine:
        return _sapi5_engine

    import dragonfly.engines.engine_sapi5 as engine_sapi5
    Sapi5Engine = engine_sapi5.Sapi5Engine

    if Sapi5Engine.is_available():
        _sapi5_engine = Sapi5Engine()
        _engine = _sapi5_engine
        return _sapi5_engine
    return None
