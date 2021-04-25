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

# pylint: disable=global-statement

import logging
import os

from .base import EngineBase, EngineError, MimicFailure


# ---------------------------------------------------------------------------

_default_engine = None
_engines_by_name = {}


def get_engine(name=None, **kwargs):
    """
        Get the engine implementation.

        This function will initialize an engine instance using the
        ``get_engine`` and ``is_engine_available`` functions in the engine
        packages and return an instance of the first available engine.  If
        one has already been initialized, it will be returned instead.

        If no specific engine is requested and no engine has already been
        initialized, this function will initialize and return an instance of
        the first available engine in the following order:

         =======================   =========================================
         SR engine back-end        Engine name string(s)
         =======================   =========================================
         1. Dragon/Natlink         ``"natlink"``
         2. Kaldi                  ``"kaldi"``
         3. WSR/SAPI 5             ``"sapi5", "sapi5inproc", "sapi5shared"``
         4. CMU Pocket Sphinx      ``"sphinx"``
         =======================   =========================================

        The :ref:`Text-input engine <RefTextEngine>` can be initialized by
        specifying ``"text"`` as the engine name.  This back-end will
        **not** be initialized if no specific engine is requested because
        the back-end is not a real SR engine and is used mostly for testing.

        **Arguments**:

        :param name: optional human-readable name of the engine to return.
        :type name: str
        :param \\**kwargs: optional keyword arguments passed through to the
            engine for engine-specific configuration.
        :rtype: EngineBase
        :returns: engine instance
        :raises: EngineError
    """
    # pylint: disable=too-many-statements,too-many-branches
    global _default_engine, _engines_by_name
    log = logging.getLogger("engine")

    if name and name in _engines_by_name:
        # If the requested engine has already been initialized, return it.
        engine = _engines_by_name[name]
    elif not name and _default_engine:
        # If no specific engine is requested and an engine has already
        #  been initialized, return it.
        engine = _default_engine
    else:
        # No engine has been initialized yet.
        engine = None

    # Check if there is an already initialized engine *and* custom engine
    #  initialization arguments.  This is not allowed.
    if engine and kwargs is not None and len(kwargs) > 0:
        message = ("Error: Passing get_engine arguments to an engine "
                   "that has already been initialized, hence these "
                   "arguments are ignored.")
        log.error(message)
        raise EngineError(message)

    # If there is a relevant initialized engine already, then return it.
    if engine:
        return engine

    # Check if we're on Windows. If  we're not on Windows, then we don't
    #  evaluate Windows-only engines like natlink.
    windows = os.name == 'nt'

    if not engine and windows and name in (None, "natlink"):
        # Attempt to retrieve the natlink back-end.
        try:
            from .backend_natlink import is_engine_available
            from .backend_natlink import get_engine as get_specific_engine
            if is_engine_available(**kwargs):
                engine = get_specific_engine(**kwargs)
        except Exception as e:
            message = ("Exception while initializing natlink engine:"
                       " %s" % (e,))
            log.warning(message)
            if name:
                raise EngineError(message)

    if not engine and name in (None, "kaldi"):
        # Attempt to retrieve the Kaldi back-end.
        try:
            from .backend_kaldi import is_engine_available
            from .backend_kaldi import get_engine as get_specific_engine
            if is_engine_available(**kwargs):
                engine = get_specific_engine(**kwargs)
        except Exception as e:
            message = ("Exception while initializing kaldi engine:"
                       " %s" % (e,))
            log.warning(message)
            if name:
                raise EngineError(message)

    sapi5_names = (None, "sapi5shared", "sapi5inproc", "sapi5")
    if not engine and windows and name in sapi5_names:
        # Attempt to retrieve the sapi5 back-end.
        try:
            from .backend_sapi5 import is_engine_available
            from .backend_sapi5 import get_engine as get_specific_engine
            if is_engine_available(name, **kwargs):
                engine = get_specific_engine(name, **kwargs)
        except Exception as e:
            message = ("Exception while initializing sapi5 engine:"
                       " %s" % (e,))
            log.warning(message)
            if name:
                raise EngineError(message)

    if not engine and name in (None, "sphinx"):
        # Attempt to retrieve the CMU Sphinx back-end.
        try:
            from .backend_sphinx import is_engine_available
            from .backend_sphinx import get_engine as get_specific_engine
            if is_engine_available(**kwargs):
                engine = get_specific_engine(**kwargs)
        except Exception as e:
            message = ("Exception while initializing sphinx engine:"
                       " %s" % (e,))
            log.warning(message)
            if name:
                raise EngineError(message)

    # Only retrieve the text input engine if explicitly specified; it is not
    #  an actual SR engine implementation and is mostly intended to be used
    #  for testing.
    if not engine and name == "text":
        # Attempt to retrieve the TextInput engine instance.
        try:
            from .backend_text import is_engine_available
            from .backend_text import get_engine as get_specific_engine
            if is_engine_available(**kwargs):
                engine = get_specific_engine(**kwargs)
        except Exception as e:
            message = ("Exception while initializing text-input engine:"
                       " %s" % (e,))
            log.warning(message)
            if name:
                raise EngineError(message)

    # Return the engine instance, if one has been initialized.  Log a
    #  message about which SR engine back-end was used.
    if engine:
        message = "Initialized %r SR engine: %r." % (engine.name, engine)
        log.info(message)
        return engine
    elif not name:
        raise EngineError("No usable engines found.")
    else:
        valid_names = ["natlink", "kaldi", "sphinx", "sapi5shared",
                       "sapi5inproc", "sapi5", "text"]
        if name not in valid_names:
            raise EngineError("Requested engine %r is not a valid engine "
                              "name." % (name,))
        else:
            raise EngineError("Requested engine %r not available."
                              % (name,))


def get_current_engine():
    """
        Get the currently initialized SR engine object.

        If an SR engine has not been initialized yet, ``None`` will be
        returned instead.

        :rtype: EngineBase | None
        :returns: engine object or None

        Usage example:

        .. code-block:: python

           # Print the name of the current engine if one has been
           # initialized.
           from dragonfly import get_current_engine
           engine = get_current_engine()
           if engine:
               print("Engine name: %r" % engine.name)
           else:
               print("No engine has been initialized.")

    """
    global _default_engine
    return _default_engine


# ---------------------------------------------------------------------------

def register_engine_init(engine):
    """
        Register initialization of an engine.

        This function sets the default engine to the first engine
        initialized.

    """

    global _default_engine, _engines_by_name
    if not _default_engine:
        _default_engine = engine
    if engine and engine.name not in _engines_by_name:
        _engines_by_name[engine.name] = engine
