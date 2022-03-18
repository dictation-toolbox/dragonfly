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
SpeakerBase class
============================================================================

"""

import logging

import dragonfly.engines

#---------------------------------------------------------------------------

class SpeakerBase(object):
    """ Base Speaker class for text-to-speech back-ends. """

    _log = logging.getLogger("speaker")
    _name = "base"

    def _register(self):
        # Register initialization of this speaker.
        dragonfly.engines.register_speaker_init(self)

    @property
    def name(self):
        """ The human-readable name of this speaker. """
        return self._name

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        raise NotImplementedError("Virtual method not implemented.")
