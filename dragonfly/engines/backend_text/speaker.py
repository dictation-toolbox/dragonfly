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
TextSpeaker class
============================================================================

"""

from dragonfly.engines.base.speaker import SpeakerBase

#---------------------------------------------------------------------------

class TextSpeaker(SpeakerBase):
    """
    This speaker class is used as a fallback when no real speaker
    implementation is available.  Specified text is written to *stdout*,
    i.e., it is printed to the console.
    """

    _name = "text"

    def __init__(self):
        self._register()

    def speak(self, text):
        self._log.warning("No text-to-speech is available, printing"
                          " specified text.")
        print(text)
