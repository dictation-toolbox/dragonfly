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
SR back-end package for SAPI 5
============================================================================

"""

import logging
_log = logging.getLogger("engine.sapi5")


#---------------------------------------------------------------------------

# Module level singleton instance of this engine implementation.
_engine = None


def is_engine_available():
    """ Check whether SAPI is available. """
    global _engine
    if _engine:
        return True

    # Attempt to import win32 package required for COM.
    try:
        from win32com.client import Dispatch
        from pywintypes import com_error
    except Exception as e:
        _log.exception("COM error during dispatch: %s" % (e,))
        return False

    # Attempt to connect to SAPI.
    try:
        Dispatch("SAPI.SpSharedRecognizer")
    except com_error as e:
        _log.exception("COM error during dispatch: %s" % (e,))
        return False
    except Exception as e:
        _log.exception("Exception during Sapi5.isNatSpeakRunning(): %s" % (e,))
        return False
    return True


def get_engine():
    """ Retrieve the Sapi5 back-end engine object. """
    global _engine
    if not _engine:
        from .engine import Sapi5Engine
        _engine = Sapi5Engine()
    return _engine
