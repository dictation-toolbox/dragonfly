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

#---------------------------------------------------------------------------

_default_engine = None
_engines_by_name = {}

_default_speaker = None
_speakers_by_name = {}

_sapi5_names = ("sapi5shared", "sapi5inproc", "sapi5")
_valid_engine_names = ("natlink", "kaldi", "sphinx", "text") + _sapi5_names
_valid_speaker_names = ("natlink", "text", "espeak", "flite") + _sapi5_names



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

    # Check if we're on Windows.  If we're not on Windows, then we don't
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

    if not engine and windows and name in (None,) + _sapi5_names:
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
        if name not in _valid_engine_names:
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


#---------------------------------------------------------------------------

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


#---------------------------------------------------------------------------

def get_speaker(name=None):
    """
        Get the text-to-speech (speaker) implementation.

        This function will initialize and return a speaker instance instance
        of the available speaker back-end.  If one has already been
        initialized, it will be returned instead.

        If no specific speaker back-end is requested and no speaker has
        already been initialized, this function will initialize and return
        an instance of the first available back-end in the following order:

         =======================   =========================================
         TTS speaker back-end      Speaker name string(s)
         =======================   =========================================
         1. SAPI 5                 ``"sapi5"``
         2. Dragon/Natlink         ``"natlink"``
         3. eSpeak                 ``"espeak"``
         4. CMU Flite              ``"flite"``
         5. Text (stdout)          ``"text"``
         =======================   =========================================

        The first two speaker back-ends are only available on Microsoft
        Windows.  The second requires that Dragon NaturallySpeaking and
        Natlink are installed on the system.

        The third and fourth back-ends, eSpeak and CMU Flite, may be used on
        most platforms.  These require that the appropriate command-line
        programs are installed on the system.

        The last back-end (text) is used as a fallback when no real speaker
        implementation is available.  This back-end writes input text to
        stdout, i.e., prints text to the console.

        **Arguments**:

        :param name: optional human-readable name of the speaker to return.
        :type name: str
        :rtype: SpeakerBase
        :returns: speaker instance
        :raises: EngineError
    """
    global _default_speaker, _speakers_by_name
    log = logging.getLogger("speaker")

    if name and name in _speakers_by_name:
        speaker = _speakers_by_name[name]
    elif not name and _default_speaker:
        speaker = _default_speaker
    else:
        speaker = None
    if speaker:
        return speaker

    windows = os.name == 'nt'
    if not speaker and windows and name in (None,) + _sapi5_names:
        # Check if the sapi5 back-end is available.
        try:
            from .backend_sapi5          import is_engine_available
            from .backend_sapi5.speaker  import Sapi5Speaker
            if is_engine_available(name):
                speaker = Sapi5Speaker()
        except Exception as e:
            message = ("Exception while initializing sapi5 speaker:"
                       " %s" % (e,))
            log.warning(message)
            if name:
                raise EngineError(message)

    if not speaker and windows and name in (None, "natlink"):
        # Check if the natlink back-end is available.
        try:
            from .backend_natlink          import is_engine_available
            from .backend_natlink.speaker  import NatlinkSpeaker
            if is_engine_available():
                speaker = NatlinkSpeaker()
        except Exception as e:
            message = ("Exception while initializing natlink speaker:"
                       " %s" % (e,))
            log.warning(message)
            if name:
                raise EngineError(message)

    if not speaker and name in (None, "espeak"):
        # Check if eSpeak is available.
        try:
            from .base.speaker_stdin import EspeakSpeaker
            if EspeakSpeaker.is_available():
                speaker = EspeakSpeaker()
        except Exception as e:
            message = ("Exception while initializing eSpeak speaker:"
                       " %s" % (e,))
            log.warning(message)
            if name:
                raise EngineError(message)

    if not speaker and name in (None, "flite"):
        # Check if CMU Flite is available.
        try:
            from .base.speaker_stdin import FliteSpeaker
            if FliteSpeaker.is_available():
                speaker = FliteSpeaker()
        except Exception as e:
            message = ("Exception while initializing Flite speaker:"
                       " %s" % (e,))
            log.warning(message)
            if name:
                raise EngineError(message)

    if not speaker and name in (None, "text"):
        # Check if the text back-end is available.
        try:
            from .backend_text          import is_engine_available
            from .backend_text.speaker  import TextSpeaker
            if is_engine_available():
                speaker = TextSpeaker()
        except Exception as e:
            message = ("Exception while initializing text speaker:"
                       " %s" % (e,))
            log.warning(message)
            if name:
                raise EngineError(message)

    # Return the speaker instance, if one has been initialized.  Log a
    #  message about which SR speaker back-end was used.
    if speaker:
        message = "Initialized %r speaker: %r." % (speaker.name, speaker)
        log.info(message)
        return speaker
    elif not name:
        raise EngineError("No usable speakers found.")
    else:
        if name not in _valid_speaker_names:
            raise EngineError("Requested speaker %r is not a valid speaker "
                              "name." % (name,))
        else:
            raise EngineError("Requested speaker %r not available."
                              % (name,))


#---------------------------------------------------------------------------

def register_speaker_init(speaker):
    """
        Register initialization of a speaker.

        This function sets the default speaker to the first speaker
        initialized.

    """

    global _default_speaker, _speakers_by_name
    if not _default_speaker:
        _default_speaker = speaker
    if speaker and speaker.name not in _speakers_by_name:
        _speakers_by_name[speaker.name] = speaker
