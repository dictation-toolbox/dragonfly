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

import inspect

import six

from .recobs import RecognitionObserver


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

    def on_begin(self):
        """"""
        if self._event == "on_begin" and callable(self._function):
            self._function()

    def _get_function_parameter_names(self):
        # Py2/3 compatible method for getting the 'args' and 'varkw' values
        # for a function object (avoids deprecation warnings in Py3).
        if six.PY2:
            argspec = inspect.getargspec(self._function)
        else:
            argspec = inspect.getfullargspec(self._function)
        return argspec[0], argspec[2]

    def on_recognition(self, words, rule, node):
        """"""
        if self._event == "on_recognition" and callable(self._function):
            arg_names, kwargs_name = self._get_function_parameter_names()
            kwargs = dict(rule=rule, node=node)
            if not kwargs_name:
                kwargs = { k: v for (k, v) in kwargs.items() if k in arg_names }
            self._function(words, **kwargs)

    def on_failure(self):
        """"""
        if self._event == "on_failure" and callable(self._function):
            self._function()

    def on_end(self):
        """"""
        if self._event == "on_end" and callable(self._function):
            self._function()

    def on_post_recognition(self, words, rule, node):
        """"""
        if self._event == "on_post_recognition" and callable(self._function):
            arg_names, kwargs_name = self._get_function_parameter_names()
            kwargs = dict(rule=rule, node=node)
            if not kwargs_name:
                kwargs = { k: v for (k, v) in kwargs.items() if k in arg_names }
            self._function(words, **kwargs)


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
