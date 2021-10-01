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
SR back-end package for Kaldi
============================================================================

"""

import logging
import struct
import sys

_log = logging.getLogger("engine.kaldi")


#---------------------------------------------------------------------------

# Module level singleton instance of this engine implementation.
_engine = None


def is_engine_available(**kwargs):
    """ Check whether Kaldi is available. """
    global _engine
    if _engine:
        return True

    if struct.calcsize("P") == 4:  # 32-bit
        _log.warning("The Python environment is 32-bit.  Kaldi requires a "
                     "64-bit python environment.")
        return False

    if sys.version_info.major < 3 or sys.version_info.minor < 6:
        _log.warning("This version of Python is not compatible with the "
                     "Kaldi back-end.  Python version 3.6 or higher is "
                     "required.")
        return False

    # Attempt to import the engine class from the module.
    try:
        from .engine import KaldiEngine
        return True
    except ImportError as e:
        _log.warning("Failed to import from Kaldi engine module: %s", e)
        return False
    except Exception as e:
        _log.exception("Exception during import of Kaldi engine module: %s",
                       e)
        return False

    return True


def get_engine(**kwargs):
    """ Retrieve the Kaldi back-end engine object. """
    global _engine
    if not _engine:
        from .engine import KaldiEngine
        _engine = KaldiEngine(**kwargs)
    return _engine
