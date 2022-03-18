#
# This file is part of Dragonfly.
# (c) Copyright 2022 by Dane Finlay
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
Stdin Speaker classes
============================================================================

"""

from __future__                      import print_function

from locale                          import getpreferredencoding
from subprocess                      import Popen, PIPE
import sys

from six                             import text_type, binary_type

from dragonfly.engines.base.speaker  import SpeakerBase

#---------------------------------------------------------------------------

class StdinSpeakerBase(SpeakerBase):

    _read_stdin_command = []

    @classmethod
    def is_available(cls):
        raise NotImplementedError("Virtual method not implemented.")

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        if len(self._read_stdin_command) == 0:
            raise NotImplementedError("Virtual method not implemented.")

        # Encode input, if necessary.
        encoding = getpreferredencoding()
        if isinstance(text, text_type):
            text = text.encode(encoding)

        # Speak *text* using the specified command.
        p = Popen(self._read_stdin_command, stdout=PIPE, stdin=PIPE,
                  stderr=PIPE)
        stdout, stderr = p.communicate(input=text)
        returncode = p.wait()

        # Decode output if it is binary.
        if isinstance(stdout, binary_type): stdout = stdout.decode(encoding)
        if isinstance(stderr, binary_type): stderr = stderr.decode(encoding)
        if stdout: print(stdout)
        if stderr: print(stderr, file=sys.stderr)

        # Handle non-zero return codes.
        if returncode != 0:
            raise RuntimeError("%s exited with non-zero return code %d"
                               % (self.name, p.returncode))


#---------------------------------------------------------------------------

class EspeakSpeaker(StdinSpeakerBase):
    """
    This speaker class uses eSpeak to synthesize specified text into speech.

    The ``espeak`` command-line program must be installed in order to use
    this implementation.  eSpeak is available on most platforms.
    """

    _name = "espeak"
    _read_stdin_command = ["espeak", "--stdin"]

    @classmethod
    def is_available(cls):
        # Check whether the *espeak* command-line program is available.
        try:
            p = Popen(["espeak", "--version"], stdout=PIPE, stderr=PIPE)
            p.communicate()
            return p.wait() == 0
        except OSError:
            return False

    def __init__(self):
        self._register()


#---------------------------------------------------------------------------

class FliteSpeaker(StdinSpeakerBase):
    """
    This speaker class uses CMU Flite to synthesize specified text into
    speech.

    The ``flite`` command-line program must be installed in order to use
    this implementation.  CMU Flite is available on most platforms.
    """

    _name = "flite"
    _read_stdin_command = ["flite"]

    @classmethod
    def is_available(cls):
        # Check whether the *flite* command-line program is available.
        try:
            p = Popen(["flite", "--version"], stdout=PIPE, stderr=PIPE)
            p.communicate()
            return p.wait() == 1
        except OSError:
            return False

    def __init__(self):
        self._register()
