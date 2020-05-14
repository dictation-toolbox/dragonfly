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
Recognition state change callbacks
----------------------------------------------------------------------------

"""

from .recobs import RecognitionObserver

try:
    from inspect import getfullargspec as getargspec
except ImportError:
    # Fallback on the deprecated function.
    from inspect import getargspec


class CallbackRecognitionObserver(RecognitionObserver):
    """
    Observer class for calling recognition state change callbacks.

    This class is used by the ``register_*_callback`` functions and is
    registered with the current engine on initialization.

    Constructor arguments:
     - *event* (*str*) -- the name of the recognition event to register for
       (e.g. ``"on_begin"``).
     - *function* (*callable*) -- function to call on the specified
       recognition event.

    """
    def __init__(self, event, function):
        RecognitionObserver.__init__(self)
        if not hasattr(self, event):
            raise ValueError("'%s' is not a valid recognition event"
                             % event)
        if not callable(function):
            raise TypeError("callback function for event '%s' is not "
                            "callable" % event)
        self._function = function
        self._event = event
        self.register()

    def _process_recognition_event(self, cb_name, required_names, **kwargs):
        if not (self._event == cb_name and callable(self._function)):
            return

        # If the callback function takes keyword arguments, only send those
        # that it accepts. Always pass required names.
        func_kwargs = kwargs
        if func_kwargs:
            argspec = getargspec(self._function)
            arg_names, kwargs_names = argspec[0], argspec[2]
            if not kwargs_names:
                func_kwargs = {k: v for (k, v) in func_kwargs.items()
                               if k in arg_names or k in required_names}

        # Call the callback function.
        self._function(**func_kwargs)

    def on_begin(self):
        """"""
        self._process_recognition_event("on_begin", [])

    def on_recognition(self, words, rule, node, results):
        """"""
        self._process_recognition_event("on_recognition", ["words"],
                                        words=words, rule=rule, node=node,
                                        results=results)

    def on_failure(self, results):
        """"""
        self._process_recognition_event("on_failure", [], results=results)

    def on_end(self, results):
        """"""
        self._process_recognition_event("on_end", [], results=results)

    def on_post_recognition(self, words, rule, node, results):
        """"""
        self._process_recognition_event("on_post_recognition", ["words"],
                                        words=words, rule=rule, node=node,
                                        results=results)


def register_beginning_callback(function):
    """
    Register a callback function to be called when speech starts.

    The :class:`CallbackRecognitionObserver` object returned from this
    function can be used to unregister the callback function.

    :param function: callback function
    :type function: callable
    :returns: recognition observer
    :rtype: CallbackRecognitionObserver
    """
    return CallbackRecognitionObserver("on_begin", function)


def register_recognition_callback(function):
    """
    Register a callback function to be called on recognition success.

    The :class:`CallbackRecognitionObserver` object returned from this
    function can be used to unregister the callback function.

    :param function: callback function
    :type function: callable
    :returns: recognition observer
    :rtype: CallbackRecognitionObserver
    """
    return CallbackRecognitionObserver("on_recognition", function)


def register_failure_callback(function):
    """
    Register a callback function to be called on recognition failures.

    The :class:`CallbackRecognitionObserver` object returned from this
    function can be used to unregister the callback function.

    :param function: callback function
    :type function: callable
    :returns: recognition observer
    :rtype: CallbackRecognitionObserver
    """
    return CallbackRecognitionObserver("on_failure", function)


def register_ending_callback(function):
    """
    Register a callback function to be called when speech ends, either
    successfully (after calling the recognition callback) or in failure
    (after calling the failure callback).

    The :class:`CallbackRecognitionObserver` object returned from this
    function can be used to unregister the callback function.

    :param function: callback function
    :type function: callable
    :returns: recognition observer
    :rtype: CallbackRecognitionObserver
    """
    return CallbackRecognitionObserver("on_end", function)


def register_post_recognition_callback(function):
    """
    Register a callback function to be called after all rule processing
    has completed after recognition success.

    The :class:`CallbackRecognitionObserver` object returned from this
    function can be used to unregister the callback function.

    :param function: callback function
    :type function: callable
    :returns: recognition observer
    :rtype: CallbackRecognitionObserver
    """
    return CallbackRecognitionObserver("on_post_recognition", function)
