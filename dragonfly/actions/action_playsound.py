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
PlaySound action
============================================================================

The :class:`PlaySound` action class is used to play wave files.


Example usage
----------------------------------------------------------------------------

The following example shows how to play a wave file using the
:class:`PlaySound` action class::

    PlaySound(file="tada.wav").execute()


Windows
----------------------------------------------------------------------------

On Windows, :class:`PlaySound` uses the `PlaySound Windows API function
<https://docs.microsoft.com/en-us/windows/win32/multimedia/the-playsound-function>`__.

The action can be used to play Windows system sounds. For example::

    # Play the system shutdown sound.
    PlaySound("SystemExit").execute()

    # Play the logout sound.
    PlaySound("WindowsLogout").execute()


System sound names are matched against registry keys.

Invalid file paths or unknown system sounds will result in the default error
sound being played. ``RuntimeErrors`` will be raised if Windows fails to
play a known system sound.


Other platforms
----------------------------------------------------------------------------

On other platforms, the :class:`PlaySound` class will use `PyAudio
<http://people.csail.mit.edu/hubert/pyaudio>`__ to play specified wave
files.

Invalid file paths will result in errors on other platforms.


Class reference
----------------------------------------------------------------------------

"""

# pylint: disable=E0401,C0413
# This file imports from optional or Win32-only packages depending on the
# platform.

from ctypes import CFUNCTYPE, c_char_p, c_int, cdll

import os
import wave

if os.name == 'nt':
    import winsound

try:
    import pyaudio
except ImportError:
    pyaudio = None

from .action_base         import ActionBase


#---------------------------------------------------------------------------

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int,
                               c_char_p)


def _get_pa_instance():
    # Suppress initial ALSA messages if using ALSA.
    # Got this from: https://stackoverflow.com/a/17673011/12157649
    try:
        asound = cdll.LoadLibrary('libasound.so')
        c_error_handler = ERROR_HANDLER_FUNC(
            lambda filename, line, function, err, fmt: None
        )
        asound.snd_lib_error_set_handler(c_error_handler)
    except:
        # We'll most likely get here if the Port Audio host API isn't ALSA.
        asound = None

    # Create the pa instance.
    pa = pyaudio.PyAudio()

    # If necessary, restore the original error handler.
    if asound:
        asound.snd_lib_error_set_handler(None)
    return pa


def _pyaudio_play(name):
    if not name:
        return

    if pyaudio is None:
        # Raise an error because pyaudio isn't installed.
        raise RuntimeError("pyaudio must be installed to use PlaySound "
                           "on this platform")

    # Play the wave file.
    pa = _get_pa_instance()
    chunk = 1024
    wf = wave.open(name, 'rb')
    stream = pa.open(format=pa.get_format_from_width(wf.getsampwidth()),
                     channels=wf.getnchannels(), rate=wf.getframerate(),
                     output=True)
    data = wf.readframes(chunk)
    while data:
        stream.write(data)
        data = wf.readframes(chunk)

    stream.stop_stream()
    stream.close()
    pa.terminate()


class PlaySound(ActionBase):
    """
        Start playing a wave file or system sound.

        When this action is executed, the specified wave file or named
        system sound is played.

        Playing named system sounds is only supported on Windows.

    """

    def __init__(self, name='', file=None):
        """
            Constructor arguments:
             - *name* (*str*, default *empty string*) --
               name of the Windows system sound to play. This argument is
               effectively an alias for *file* on other platforms.
             - *file* (*str*, default *None*) --
               path of wave file to play when the action is executed.

            If *name* and *file* are both *None*, then waveform playback
            will be silenced on Windows when the action is executed. Nothing
            will happen on other platforms.

        """
        ActionBase.__init__(self)
        self._flags = 0
        if file is not None:
            self._name = file
            if os.name == 'nt':
                self._flags = winsound.SND_FILENAME
        else:
            self._name = name
            if os.name == 'nt':
                self._flags = winsound.SND_ALIAS

        # Expand ~ constructions and shell variables in the file path if
        # necessary.
        if file is not None or os.name != 'nt':
            self._name = os.path.expanduser(os.path.expandvars(self._name))

        self._str = str(self._name)

    def _execute(self, data=None):
        if os.name == 'nt':
            # Play the file or sound using the Windows API.
            winsound.PlaySound(self._name, self._flags)
        else:
            # Play the file with pyaudio.
            _pyaudio_play(self._name)
