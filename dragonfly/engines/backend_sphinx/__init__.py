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
SR back-end package for CMU Sphinx/Pocket Sphinx
============================================================================

"""

import logging
_log = logging.getLogger("engine.sphinx")


# Module level singleton instance of this engine implementation.
_engine = None


def is_engine_available():
    """ Check whether Sphinx is available. """
    global _engine
    if _engine:
        return True

    # TODO Attempt to communicate with Sphinx somehow
    try:
        pass
    except Exception, e:
        _log.info("Failed to connect to Sphinx process: %s" % (e,))
        return False


def get_engine():
    """ Retrieve the Natlink back-end engine object. """
    global _engine
    if not _engine:
        from .engine import SphinxEngine
        _engine = SphinxEngine()
    return _engine
