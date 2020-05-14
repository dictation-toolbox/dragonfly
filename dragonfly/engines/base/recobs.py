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

import logging

try:
    from inspect import getfullargspec as getargspec
except ImportError:
    # Fallback on the deprecated function.
    from inspect import getargspec

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

    def _process_observer_callbacks(self, cb_name, required_names,
                                    **kwargs):
        for observer in self._observers:
            func = getattr(observer, cb_name, None)
            if not func:
                continue

            # If the callback function takes keyword arguments, only send
            # those that it accepts. Always pass required names.
            func_kwargs = kwargs
            if func_kwargs:
                argspec = getargspec(func)
                arg_names, kwargs_names = argspec[0], argspec[2]
                if not kwargs_names:
                    func_kwargs = {k: v for (k, v) in func_kwargs.items()
                                   if k in arg_names or k in required_names}

            # Call the callback function, catching and logging exceptions.
            try:
                func(**func_kwargs)
            except Exception as e:
                self._log.exception("Exception during %s()"
                                    " method of recognition observer %s: %s"
                                    % (cb_name, observer, e))

    def notify_begin(self):
        self._process_observer_callbacks("on_begin", [])

    def notify_recognition(self, words, rule, node, results):
        self._process_observer_callbacks("on_recognition", ["words"],
                                         words=words, rule=rule, node=node,
                                         results=results)
        self.notify_end(results)

    def notify_failure(self, results):
        self._process_observer_callbacks("on_failure", [], results=results)
        self.notify_end(results)

    def notify_end(self, results):
        self._process_observer_callbacks("on_end", [], results=results)

    def notify_post_recognition(self, words, rule, node, results):
        self._process_observer_callbacks("on_post_recognition", ["words"],
                                         words=words, rule=rule, node=node,
                                         results=results)

    def _activate(self):
        raise NotImplementedError(str(self))

    def _deactivate(self):
        raise NotImplementedError(str(self))
