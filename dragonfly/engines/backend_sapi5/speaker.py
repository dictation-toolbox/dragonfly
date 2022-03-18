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
SAPI 5 text-to-speech class
============================================================================

"""

from win32com.client            import Dispatch
from win32com.client.gencache   import EnsureDispatch

from dragonfly.engines.base.speaker import SpeakerBase

#---------------------------------------------------------------------------

class Sapi5Speaker(SpeakerBase):
    """
    This speaker class uses the SAPI 5 text-to-speech functionality.  It is
    available on Microsoft Windows Vista and above.

    It has no specific requirements other than the pywin32 library, which is
    required to use Dragonfly on Microsoft Windows.
    """

    _name = "sapi5"

    def __init__(self):
        EnsureDispatch("SAPI.SpVoice")
        self._spvoice = Dispatch("SAPI.SpVoice")
        self._register()

    def speak(self, text):
        self._spvoice.Speak(text)
