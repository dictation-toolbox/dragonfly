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
Engine base class
============================================================================

"""

from ..log import get_log


#---------------------------------------------------------------------------

class EngineBase(object):
    """ Base class for engine-specific back-ends. """

    _log = get_log("engine")
    _name = "base"

    @classmethod
    def is_available(cls):
        """ Check whether this engine is available. """
        return False

    #-----------------------------------------------------------------------

    def __str__(self):
        return "%s()" % self.__class__.__name__

    @property
    def name(self):
        """ The human-readable name of this engine. """
        return self._name

    #-----------------------------------------------------------------------
    # Methods for working with grammars.

    def load_grammar(self, grammar, *args, **kwargs):
        raise NotImplementedError("Engine %s not implemented." % self)

    def update_list(self, lst, grammar):
        raise NotImplementedError("Engine %s not implemented." % self)


    #-----------------------------------------------------------------------
    # Recognition observer methods.

    def register_recognition_observer(self, observer):
        self._recognition_observer_manager.register(observer)

    def unregister_recognition_observer(self, observer):
        self._recognition_observer_manager.unregister(observer)

    def enable_recognition_observers(self):
        self._recognition_observer_manager.enable()

    def disable_recognition_observers(self):
        self._recognition_observer_manager.disable()


    #-----------------------------------------------------------------------
    #  Miscellaneous methods.

    def mimic(self, words):
        """ Mimic a recognition of the given *words*. """
        raise NotImplementedError("Engine %s not implemented." % self)

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        raise NotImplementedError("Engine %s not implemented." % self)

    def _get_language(self):
        raise NotImplementedError("Engine %s not implemented." % self)
    language = property(fget=lambda self: self._get_language(),
                        doc="Current user language of the SR engine.")
