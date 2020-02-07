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
SR back-end package for CMU Pocket Sphinx
============================================================================

The main interface to this engine is provided by methods and properties of
the engine class. Please see the :ref:`CMU Pocket Sphinx engine page
<RefSphinxEngine>` for more details.

"""

import logging
_log = logging.getLogger("engine.sphinx")


# Module level singleton instance of this engine implementation.
_engine = None


def is_engine_available():
    """ Check whether the Sphinx engine is available. """
    if _engine:
        return True

    # Attempt to import the engine class from the module.
    try:
        from .engine import SphinxEngine
        return True
    except ImportError as e:
        _log.warning("Failed to import from Sphinx engine module: %s", e)
        return False
    except Exception as e:
        _log.exception("Exception during import of Sphinx engine module: "
                       "%s", e)
        return False

    return True


def get_engine():
    """ Retrieve the Sphinx back-end engine object. """
    global _engine
    if not _engine:
        from .engine import SphinxEngine
        _engine = SphinxEngine()
    return _engine
