#
# This file is part of Dragonfly.
# (c) Copyright 2021 by Dane Finlay
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
DNS and Natlink text-to-speech class
============================================================================

"""

import natlink

from dragonfly.engines.base.speaker import SpeakerBase

#---------------------------------------------------------------------------

class NatlinkSpeaker(SpeakerBase):

    _name = "natlink"

    def __init__(self):
        self._register()

    def speak(self, text):
        # Store the current mic state.
        mic_state = natlink.getMicState()

        # Say the text.
        natlink.execScript('TTSPlayString "%s"' % text)

        # Restore the previous mic state if necessary.  This is done for
        #  consistent behaviour for each supported version of DNS.
        if mic_state != natlink.getMicState():
            natlink.setMicState(mic_state)
