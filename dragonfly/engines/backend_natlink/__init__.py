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
SR back-end package for DNS and Natlink
============================================================================

"""

from ...log import get_log
_log = get_log("engine.natlink")


#---------------------------------------------------------------------------

# Module level singleton instance of this engine implementation.
engine = None


def is_engine_available():
    """ Check whether Natlink is available. """
    global engine
    if engine:
        return True

    # Attempt to import natlink.
    try:
        import natlink
    except ImportError, e:
        _log.info("Failed to import natlink package: %s" % (e,))
        return False
    except Exception, e:
        _log.exception("Exception during import of natlink package: %s" % (e,))
        return False

    try:
        if natlink.isNatSpeakRunning():
            return True
        else:
        # LOG.
            return False
    except Exception, e:
        _log.exception("Exception during natlink.isNatSpeakRunning(): %s" % (e,))
        return False


def get_engine():
    """ Retrieve the Natlink back-end engine object. """
    global engine
    if not engine:
        from .engine import NatlinkEngine
        engine = NatlinkEngine()
    return engine
