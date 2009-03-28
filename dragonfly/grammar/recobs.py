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
Recognition observer base class
============================================================================

"""

from ..log import get_log
from ..engines.engine import get_engine


#---------------------------------------------------------------------------

class RecognitionObserver(object):

    _log = get_log("engine")

    def __init__(self):
        pass

    def __del__(self):
        try:
            self.unregister()
        except Exception, e:
            pass

    def register(self):
        engine = get_engine()
        engine.register_recognition_observer(self)

    def unregister(self):
        engine = get_engine()
        engine.unregister_recognition_observer(self)

#    def on_recognition(self, result, words):
#        pass
#
#    def on_failure(self, result):
#        pass
