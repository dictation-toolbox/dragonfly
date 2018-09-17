﻿#
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

import logging


#---------------------------------------------------------------------------

class RecObsManagerBase(object):

    _log = logging.getLogger("engine.recobs")

    def __init__(self, engine):
        self._engine = engine
        self._enabled = True
        self._observers = []
        self._observer_ids = set()

    def enable(self):
        if not self._enabled:
            self._enabled = True
            self._activate()

    def disable(self):
        if self._enabled:
            self._enabled = False
            self._deactivate()

    def register(self, observer):
        if id(observer) in self._observer_ids:
            return
        elif not self._observers:
            self._activate()
        self._observers.append(observer)
        self._observer_ids.add(id(observer))

    def unregister(self, observer):
        try:
            self._observers.remove(observer)
            self._observer_ids.remove(id(observer))
        except ValueError:
            pass
        else:
            if not self._observers:
                self._deactivate()

    def notify_begin(self):
        for observer in self._observers:
            try:
                if hasattr(observer, "on_begin"):
                    observer.on_begin()
            except Exception as e:
                self._log.exception("Exception during on_begin()"
                                    " method of recognition observer %s: %s"
                                    % (observer, e))

    def notify_recognition(self, words):
        for observer in self._observers:
            try:
                if hasattr(observer, "on_recognition"):
                    observer.on_recognition(words)
            except Exception as e:
                self._log.exception("Exception during on_recognition()"
                                    " method of recognition observer %s: %s"
                                    % (observer, e))

    def notify_failure(self):
        for observer in self._observers:
            try:
                if hasattr(observer, "on_failure"):
                    observer.on_failure()
            except Exception as e:
                self._log.exception("Exception during on_failure()"
                                    " method of recognition observer %s: %s"
                                    % (observer, e))

    def _activate(self):
        raise NotImplementedError(str(self))

    def _deactivate(self):
        raise NotImplementedError(str(self))
