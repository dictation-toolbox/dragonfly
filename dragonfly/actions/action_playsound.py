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

This section describes the :class:`PlaySound` action object.  This
type of action is used to play sounds or sound files.


Example PlaySound uses
----------------------------------------------------------------------------

The following example shows how to play a wave file using an
:class:`PlaySound` action object::

    PlaySound(file=r"C:\\Windows\\media\\tada.wav").execute()


PlaySound on Windows
----------------------------------------------------------------------------

The behavior of the :class:`PlaySound` action object differs between
platforms.  On Windows, it may be used to play Windows system sounds.
This is achieved via the *name* parameter.  For example::

    # Play the logon sound.
    PlaySound("WindowsLogon").execute()

    # Play the system shutdown sound.
    PlaySound("SystemExit").execute()

For this to work, the specified name must be listed (without spaces)
in the Windows *Sound* control panel window, in the *Sounds* tab.
If an invalid file path, or an unknown system sound, is specified,
the default error sound will be played.


PlaySound on macOS and Linux
----------------------------------------------------------------------------

On macOS and Linux, the :class:`PlaySound` action object uses the
`sounddevice <https://python-sounddevice.readthedocs.io/>`__ and
`soundfile <https://python-soundfile.readthedocs.io/>`__ packages to
play specified wave files.  The *numpy* package may also need to be
installed.  These dependencies may be installed by running the
following command: ::

    $ pip install 'dragonfly2[playsound]'

The *name* parameter is an alias for *file* on these platforms.


Class reference
----------------------------------------------------------------------------

"""

import os

from dragonfly.actions.action_base import ActionBase


#---------------------------------------------------------------------------
# Define the *play* function.

if os.name == "nt":
    import winsound
    play = winsound.PlaySound

else:
    # Take the same arguments as the winsound function.
    def play(name, flags):
        if not name:
            return

        import sounddevice as sd
        import soundfile as sf

        data, fs = sf.read(name)
        sd.play(data, fs)
        sd.wait()


#---------------------------------------------------------------------------

class PlaySound(ActionBase):
    """
        Start playing a wave file or system sound.

        When this action is executed, the specified wave file or
        named system sound is played.

        Playing named system sounds is only supported on Windows.

    """

    def __init__(self, name='', file=None):
        """
            Constructor arguments:
             - *name* (*str*, default *empty string*) --
               name of the Windows system sound to play.  This argument
               is effectively an alias for *file* on other platforms.
             - *file* (*str*, default *None*) --
               path of wave file to play when the action is executed.

            If *name* and *file* are both *None*, then waveform playback
            will be silenced on Windows when the action is executed.
            Nothing will happen on other platforms.

        """
        ActionBase.__init__(self)
        if file:
            self._name = file
            self._flags = 0x20000  # SND_FILENAME
        else:
            self._name = name
            self._flags = 0x10000  # SND_ALIAS

        # Expand ~ constructions and shell variables in the path, if
        #  necessary.
        if file or os.name != "nt":
            self._name = os.path.expanduser(os.path.expandvars(self._name))

        self._str = str(self._name)

    def _execute(self, data=None):
        # Play the specified sound or sound file.
        play(self._name, self._flags)
