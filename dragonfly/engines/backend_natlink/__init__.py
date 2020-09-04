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

import logging
import os
import platform
import struct
import sys

_log = logging.getLogger("engine.natlink")


#---------------------------------------------------------------------------

# Module level singleton instance of this engine implementation.
_engine = None


def is_engine_available(**kwargs):
    """
        Check whether Natlink is available.

        :param \\**kwargs: optional keyword arguments passed through to the
            engine for engine-specific configuration.
    """
    # pylint: disable=too-many-return-statements
    global _engine
    if _engine:
        return True

    platform_name = platform.system()
    if platform_name != 'Windows':
        _log.warning("%s is not supported by the Natlink engine backend",
                     platform_name)
        return False

    if struct.calcsize("P") == 8:  # 64-bit
        _log.warning("The python environment is 64-bit. Natlink requires a "
                     "32-bit python environment")
        return False

    # Attempt to import natlink.
    try:
        import natlink
    except ImportError as e:
        # Add Natlink's default 'core' directory path to sys.path if
        # necessary.
        coredir_path = r'C:\\NatLink\\NatLink\\MacroSystem\\core'
        pyd_filename = 'natlink.pyd'
        pyd_path = os.path.join(coredir_path, pyd_filename)
        import_failure = True
        if os.path.isdir(coredir_path):
            if not os.path.isfile(pyd_path):
                _log.warning("Requested engine 'natlink' is not available: "
                             "The %r file is missing from Natlink's core "
                             "directory", pyd_filename)
                return False

            # Add the core directory to the path and try importing again.
            sys.path.append(coredir_path)
            try:
                import natlink
                import_failure = False
            except ImportError:
                pass
        if import_failure:
            _log.warning("Requested engine 'natlink' is not available: "
                         "Natlink is not installed: %s", e)
            return False
    except Exception as e:
        _log.exception("Exception during import of natlink package: "
                       "%s", e)
        return False

    try:
        if natlink.isNatSpeakRunning():
            return True
        else:
            _log.warning("Requested engine 'natlink' is not available: "
                         "Dragon NaturallySpeaking is not running")
            return False
    except Exception as e:
        _log.exception("Exception during natlink.isNatSpeakRunning(): "
                       "%s", e)
        return False


def get_engine(**kwargs):
    """
        Retrieve the Natlink back-end engine object.

        :param \\**kwargs: optional keyword arguments passed through to the
            engine for engine-specific configuration.
    """
    global _engine
    if not _engine:
        from .engine import NatlinkEngine
        _engine = NatlinkEngine(**kwargs)
    return _engine
