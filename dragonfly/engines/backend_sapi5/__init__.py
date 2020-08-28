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
SR back-end package for WSR and SAPI 5
============================================================================

"""

import logging
import platform

_log = logging.getLogger("engine.sapi5")


#---------------------------------------------------------------------------

# Module level singleton instance of this engine implementation.
_engine = None


def is_engine_available(name, **kwargs):
    """
        Check whether SAPI is available.

        :param name: optional human-readable name of the engine to return.
        :type name: str
        :param \\**kwargs: optional keyword arguments passed through to the
            engine for engine-specific configuration.
    """
    global _engine
    if _engine:
        return True

    platform_name = platform.system()
    if platform_name != 'Windows':
        _log.warning("%s is not supported by the SAPI5 engine backend",
                     platform_name)
        return False

    # Attempt to import win32 package required for COM.
    try:
        from win32com.client import Dispatch
    except ImportError as e:
        _log.warning("Failed to import from win32com package: %s. Is it "
                     "installed?", e)
        return False

    try:
        from pywintypes import com_error
    except ImportError as e:
        _log.warning("Failed to import from the pywintypes package: %s. Is "
                     "it installed?", e)
        return False

    # Attempt to connect to SAPI using the correct dispatch name.
    from .engine import Sapi5Engine, Sapi5InProcEngine

    # Use the in-process engine by default, otherwise use the shared engine.
    if not name or name == "sapi5inproc":
        dispatch_name = Sapi5InProcEngine.recognizer_dispatch_name
    else:
        dispatch_name = Sapi5Engine.recognizer_dispatch_name
    try:
        Dispatch(dispatch_name)
    except com_error as e:
        _log.exception("COM error during dispatch: %s", e)
        return False
    except Exception as e:
        _log.exception("Exception during Sapi5 COM dispatch): %s", e)
        return False
    return True


def get_engine(name=None, **kwargs):
    """
        Retrieve the Sapi5 back-end engine object.

        :param name: optional human-readable name of the engine to return.
        :type name: str
        :param \\**kwargs: optional keyword arguments passed through to the
            engine for engine-specific configuration.
    """
    global _engine
    if not _engine:
        from .engine import Sapi5Engine, Sapi5InProcEngine
        # Use the in-process engine by default.
        if not name or name == "sapi5inproc":
            _engine = Sapi5InProcEngine(**kwargs)
        else:
            _engine = Sapi5Engine(**kwargs)
    return _engine
