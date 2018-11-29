#
# This file is part of Dragonfly.
# (c) Copyright 2007, 2008 by Christo Butcher
# (c) Copyright 2018 by David Williams-King
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
SR back-end package for Kaldi-based Voxhub.io
============================================================================
"""

import logging
_log = logging.getLogger("engine.voxhub")


# Module level singleton instance of this engine implementation.
_engine = None


def is_engine_available():
    """ Check whether the Voxhub engine is available. """
    global _engine
    if _engine:
        return True

#    try:
#        import sphinxwrapper
#    except ImportError as e:
#        _log.info("Failed to import sphinxwrapper package: %s. Is it installed?" % (e,))
#        return False
#    except Exception as e:
#        _log.info("Exception during import of sphinxwrapper package: %s" % (e,))
#        return False

    print "Voxhub engine is always available..."
    return True


def get_engine():
    """ Retrieve the Voxhub back-end engine object. """
    global _engine
    if not _engine:
        from .engine import VoxhubEngine
        _engine = VoxhubEngine()
    return _engine
