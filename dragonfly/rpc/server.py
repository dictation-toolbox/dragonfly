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
RPC server
----------------------------------------------------------------------------

Dragonfly's RPC server handles requests by processing each method through
the current engine's :ref:`multiplexing timer interface <RefEngineTimers>`.
This allows engines to handle requests safely and keeps engine-specific
implementation details out of the *dragonfly.rpc* sub-package.

Security tokens
============================================================================

The RPC server uses mandatory security tokens to authenticate client
requests. This avoids some security issues where, for example, malicious web
pages could send POST requests to the server, even if running on localhost.

If sending requests over an open network, please ensure that the connection
is secure by using TLS or SSH port forwarding.

If the server's :code:`security_token` constructor parameter is not
specified, a new token will be generated and printed to the console. Clients
must specify the security token either as the last positional argument or as
the :code:`security_token` keyword argument.

Errors will be raised if clients send no security token or a token that
doesn't match the server's.

Class reference
============================================================================

"""

import functools
import logging
import threading
import time

from decorator import decorator
from jsonrpc.dispatcher import Dispatcher as BaseDispatcher
from jsonrpc.manager import JSONRPCResponseManager
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple

from .methods import methods
from .security import compare_security_token, generate_security_token
from .util import send_rpc_request
from ..engines import get_engine


class PermissionDeniedError(Exception):
    """
    Error raised if clients send security tokens that don't match the
    server's.
    """


_log = logging.getLogger("rpc.methods")

# --------------------------------------------------------------------------
# RPC method decorator used by the server internally.

@decorator
def _rpc_method(method, *args, **kwargs):
    # Create a thread condition for waiting for the method's result.
    condition = threading.Condition()

    closure = []
    def timer_func():
        try:
            closure.append(method(*args, **kwargs))
        except Exception as e:
            # Log any exceptions.
            _log.exception("Exception occurred during RPC method '%s': %s"
                           % (method.__name__, e))
            closure.append(e)

        # Notify the waiting thread that the result is ready.
        with condition:
            condition.notify()

    # Start a non-repeating timer to execute timer_func().
    get_engine().create_timer(timer_func, 0, repeating=False)

    # Wait for the result.
    with condition:
        condition.wait()

    # Raise an error if it's an exception (json-rpc handles this),
    # otherwise return it.
    result = closure[0]
    if isinstance(result, Exception):
        raise result
    else:
        return result

# --------------------------------------------------------------------------
# JSONRPC Dispatcher sub-class.

class Dispatcher(BaseDispatcher):
    """"""

    def __init__(self, server):
        self.server = server
        super(Dispatcher, self).__init__()

    def add_method(self, f=None, name=None):
        """"""
        if name and not f:
            return functools.partial(self.add_method, name=name)
        elif not name and f:
            name = f.__name__

        if not callable(f):
            raise TypeError("f must be callable")

        def checked_rpc_method(*args, **kwargs):
            assert not (args and kwargs)

            # Pop the security token from args or kwargs. Raise an error if
            # there is no token.
            if args:
                args = list(args)
                rpc_security_token = args.pop(len(args) - 1)
            elif "security_token" in kwargs:
                rpc_security_token = kwargs.pop("security_token")
            else:
                message = ("client did not send the required "
                           "'security_token' argument")
                _log.error(message)
                raise ValueError(message)

            # Check if the received token matches the server's token.
            if not compare_security_token(self.server.security_token,
                                          rpc_security_token):
                message = ("Client sent a security token that did not match"
                           " the server\'s")
                _log.error(message)
                raise PermissionDeniedError(message)

            # The security tokens match, so execute the method.
            return f(*args, **kwargs)

        checked_rpc_method.__name__ = name
        self.method_map[name] = checked_rpc_method
        return f


# --------------------------------------------------------------------------
# RPC server class.

class RPCServer(object):
    """
    RPC server class.

    This class will run a local web server on port 50051 by default. The
    server expects requests using
    `JSON-RPC 2.0 <https://www.jsonrpc.org/specification>`__.

    Constructor arguments:

    - *address* -- address to use (*str*, default: "127.0.0.1")
    - *port* -- port to use (*int*, default: 50051)
    - *ssl_context* -- SSL context object to pass to
      *werkzeug.serving.run_simple* (*SSLContext*, default: None).
    - *threaded* -- whether to use a separate thread to process each request
      (*bool*, default: True).
    - *security_token* -- security token for authenticating clients
      (*str*, default: None). A new token will be generated and printed if
      this parameter is unspecified.

    The *ssl_context* parameter is explained in more detail in Werkzeug's
    `SSL serving documentation
    <http://werkzeug.pocoo.org/docs/0.14/serving/#ssl>`__.

    Secure connections can also be set up using OpenSSH port forwarding with
    a command such as::

        $ ssh -NTf -L 50051:127.0.0.1:50051 <system-with-rpc-server>

    *Minor note*: using an IP address instead of a hostname for the
    *address* parameter should increase performance somewhat, e.g.
    "127.0.0.1" instead of "localhost".

    .. warning::

       Do **not** send requests to the server from the main engine thread;
       thread deadlocks *will* occur if you do this because the main thread
       cannot call timer functions and wait for a response at the same time.
       The RPC framework was designed to be used from *remote* processes.

       Requests will not be processed if the engine is not connected and
       processing speech.


    """

    _log = logging.getLogger("rpc.server")

    def __init__(self, address="127.0.0.1", port=50051, ssl_context=None,
                 threaded=True, security_token=None):
        self._address = address
        self._port = port
        self._ssl_context = ssl_context
        self._threaded = threaded
        if security_token is None:
            security_token = generate_security_token()
            self._log.warning("Generating a new security token because the "
                              "'security_token' parameter was unspecified.")
            print("The generated security token is '%s'." % security_token)

        self.security_token = security_token
        self._thread = None
        self._dispatcher = Dispatcher(self)

        # Add the built-in RPC methods defined in methods.py.
        for method in methods:
            self.add_method(method)

    @Request.application
    def _application(self, request):
        # Add the shutdown method if it is available and has not already
        # been added. This won't be executed via the engine timers.
        shutdown_func = request.environ.get('werkzeug.server.shutdown')
        shutdown_func_name = "shutdown_rpc_server"
        if shutdown_func and shutdown_func_name not in self._dispatcher:
            # Add it to the dispatcher directly.
            self._dispatcher.add_method(shutdown_func, shutdown_func_name)

        # Get a response using the method dispatcher and return it.
        response = JSONRPCResponseManager.handle(
            request.data, self._dispatcher
        )
        return Response(response.json, mimetype='application/json')

    @property
    def url(self):
        """
        The URL to send JSON-RPC requests to.
        """
        # Note: this assumes any non-null SSL context is valid.
        protocol = "https" if self._ssl_context else "http"
        return "%s://%s:%d/jsonrpc" % (protocol, self._address, self._port)

    def send_request(self, method, params, id=0):
        """
        Utility method to send a JSON-RPC request to the server. This will
        block the current thread until a response is received.

        This method is mostly used for testing. If called from the engine's
        main thread, a deadlock *will* occur.

        This will raise an error if the request fails with an error or if
        the server is unreachable.

        The server's security token will automatically be added to the
        ``params`` list/dictionary.

        :param method: name of the RPC method to call.
        :param params: parameters of the RPC method to call.
        :param id: ID of the JSON-RPC request (default: 0).
        :type method: str
        :type params: list | dict
        :type id: int
        :returns: JSON-RPC response
        :rtype: dict
        :raises: RuntimeError
        """
        # Add the server's security token to params.
        security_token = self.security_token
        if isinstance(params, dict):
            params["security_token"] = security_token
        else:
            params.append(security_token)

        return send_rpc_request(self.url, method, params, id)

    def start(self):
        """
        Start the server.

        This method is non-blocking, the RPC server will run on a separate
        daemon thread. This way it is not necessary to call :meth:`stop`
        before the main thread terminates.
        """
        # Handle a previous Thread.join() timeout.
        if self._thread and not self._thread.is_alive():
            self._thread = None

        # Return if the server thread is already running.
        elif self._thread:
            return

        def run():
            # Note: 'threaded' means that each request is handled using a
            # separate thread. This introduces some overhead costs.
            try:
                return run_simple(self._address, self._port,
                                  self._application,
                                  ssl_context=self._ssl_context,
                                  threaded=self._threaded)
            except Exception as e:
                self._log.exception("Exception caught on RPC server thread:"
                                    " %s" % e)

        self._thread = threading.Thread(target=run)
        self._thread.setDaemon(True)
        self._thread.start()

        # Wait a few milliseconds to allow the server to start properly.
        time.sleep(0.1)

    def stop(self):
        """
        Stop the server if it is running.
        """
        # Handle a previous Thread.join() timeout.
        if self._thread and not self._thread.is_alive():
            self._thread = None

        # Return if the server isn't currently running.
        if not self._thread:
            return

        # werkzeug is normally stopped through a request to the server.
        self.send_request("shutdown_rpc_server", [])
        timeout = 5
        self._thread.join(timeout)
        if self._thread.is_alive():
            self._log.warning("RPC server thread failed to stop after %d "
                              "seconds" % timeout)
        else:
            self._thread = None

    def add_method(self, method, name=None):
        """
        Add an RPC method to the server.

        Restarting the server is *not* required for the new method to be
        available.

        This can be used to override method implementations if that is
        desirable.

        This method can also be used as a decorator.

        :param method: the implementation of the RPC method to add.
        :param name: optional name of the RPC method to add. If this is
            None, then :code:`method.__name__` will be used instead.
        :type method: callable
        :type name: str
        """
        if name and not method:
            return functools.partial(self.add_method, name=name)

        new_method = _rpc_method(method)
        self._dispatcher.add_method(new_method, name)

        # Return the original method.
        return method

    def remove_method(self, name):
        """
        Remove an RPC method from the server. This will not raise an error
        if the method does not exist.

        Restarting the server is *not* required for the change to take
        effect.

        :param name: the name of the RPC method to remove.
        :type name: str
        """
        self._dispatcher.pop(name, None)

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
