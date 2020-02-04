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

import logging
import os
import traceback
from .base import EngineBase, EngineError, MimicFailure


# ---------------------------------------------------------------------------

_default_engine = None
_engines_by_name = {}


def get_engine(name=None, **kwargs):
    """
        Get the engine implementation.

        This function will initialize an engine object using the
        ``get_engine`` and ``is_engine_available`` functions in the engine
        packages and return an instance of the first available engine. If
        one has already been initialized, it will be returned instead.

        :param name: optional human-readable name of the engine to return.
        :type name: str
        :param \\**kwargs: optional keyword arguments passed through to the
            engine for engine-specific configuration.
        :rtype: EngineBase
        :raises: EngineError
    """
    global _default_engine, _engines_by_name
    log = logging.getLogger("engine")

    if name and name in _engines_by_name:
        # If the requested engine has already been loaded, return it.
        return _engines_by_name[name]
    elif not name and _default_engine:
        # If no specific engine is requested and an engine has already
        #  been loaded, return it.
        return _default_engine

    # Check if we're on Windows. If name is None and we're not on Windows,
    # then we don't evaluate Windows-only engines like natlink.
    windows = os.name == 'nt'

    if (windows and not name) or name == "natlink":
        # Attempt to retrieve the natlink back-end.
        try:
            from .backend_natlink import is_engine_available
            from .backend_natlink import get_engine as get_specific_engine
            if is_engine_available(**kwargs):
                _default_engine = get_specific_engine(**kwargs)
                _engines_by_name["natlink"] = _default_engine
                return _default_engine
        except Exception as e:
            message = ("Exception while initializing natlink engine:"
                       " %s" % (e,))
            print(message)
            if name:
                raise EngineError(message)

    sapi5_names = ["sapi5shared", "sapi5inproc", "sapi5"]
    if (windows and not name) or name in sapi5_names:
        # Attempt to retrieve the sapi5 back-end.
        try:
            from .backend_sapi5 import is_engine_available
            from .backend_sapi5 import get_engine as get_specific_engine
            if is_engine_available(name, **kwargs):
                _default_engine = get_specific_engine(name, **kwargs)
                _engines_by_name["sapi5"] = _default_engine
                return _default_engine
        except Exception as e:
            message = ("Exception while initializing sapi5 engine:"
                       " %s" % (e,))
            print(message)
            if name:
                raise EngineError(message)

    if not name or name == "sphinx":
        # Attempt to retrieve the CMU Sphinx back-end.
        try:
            from .backend_sphinx import is_engine_available
            from .backend_sphinx import get_engine as get_specific_engine
            if is_engine_available(**kwargs):
                _default_engine = get_specific_engine(**kwargs)
                _engines_by_name["sphinx"] = _default_engine
                return _default_engine
        except Exception as e:
            message = ("Exception while initializing sphinx engine:"
                       " %s" % (e,))
            log.exception(message)
            if name:
                raise EngineError(message)

    if not name or name == "kaldi":
        # Attempt to retrieve the Kaldi back-end.
        try:
            from .backend_kaldi import is_engine_available
            from .backend_kaldi import get_engine as get_specific_engine
            if is_engine_available(**kwargs):
                _default_engine = get_specific_engine(**kwargs)
                _engines_by_name["kaldi"] = _default_engine
                return _default_engine
        except Exception as e:
            message = ("Exception while initializing kaldi engine:"
                       " %s" % (e,))
            print(message)
            if name:
                raise EngineError(message)

    # Only retrieve the text input engine if explicitly specified; it is not
    # an actual SR engine implementation and is mostly intended to be used
    # for testing.
    if name == "text":
        # Attempt to retrieve the TextInput engine instance.
        try:
            from .backend_text import is_engine_available
            from .backend_text import get_engine as get_specific_engine
            if is_engine_available(**kwargs):
                _default_engine = get_specific_engine(**kwargs)
                _engines_by_name["text"] = _default_engine
                return _default_engine
        except Exception as e:
            message = ("Exception while initializing text-input engine:"
                       " %s" % (e,))
            print(message)
            if name:
                raise EngineError(message)

    if not name:
        raise EngineError("No usable engines found.")
    else:
        valid_names = ["natlink", "kaldi", "sphinx", "sapi5shared"
                       "sapi5inproc", "sapi5"]
        if name not in valid_names:
            raise EngineError("Requested engine %r is not a valid engine "
                              "name." % (name,))
        else:
            raise EngineError("Requested engine %r not available."
                              % (name,))


# ---------------------------------------------------------------------------

def register_engine_init(engine):
    """
        Register initialization of an engine.

        This function sets the default engine to the first engine
        initialized.

    """

    global _default_engine
    if not _default_engine:
        _default_engine = engine
