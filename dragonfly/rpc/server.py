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

.. warning::

   Do not call engine methods directly or indirectly from other threads,
   e.g. with :meth:`engine.mimic`, :meth:`grammar.unload`,
   :meth:`grammar.load`, etc. Some engines such as natlink do not support
   multi-threading and will raise errors. In addition, the
   :code:`EngineBase` class is not thread safe.

"""

import logging
import threading
import time

from jsonrpc.manager import JSONRPCResponseManager
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple

# Import some things from .methods. This will also set up methods defined in
# that module.
from .methods import dispatcher, server_timer_function
from .util import send_rpc_request
from ..engines import get_engine
from ..log import setup_log


# Set up a logger.
_log = logging.getLogger("rpc.server")
setup_log()


@Request.application
def application(request):
    # Dispatcher is dictionary {<method_name>: callable}
    # Add a shutdown method if it is available.
    shutdown_function = request.environ.get('werkzeug.server.shutdown')
    if shutdown_function:
        dispatcher["shutdown_rpc_server"] = shutdown_function

    response = JSONRPCResponseManager.handle(
        request.data, dispatcher
    )
    return Response(response.json, mimetype='application/json')

# --------------------------------------------------------------------------

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

    The *ssl_context* parameter is explained in more detail in Werkzeug's
    `SSL serving documentation
    <http://werkzeug.pocoo.org/docs/0.14/serving/#ssl>`__.

    Secure connections can also be set up using OpenSSH port forwarding with
    a command such as::

        $ ssh -NTf -L 50051:127.0.0.1:50051 <system-with-rpc-server>

    *Minor note*: using an IP address instead of a hostname for the
    *address* parameter should increase performance somewhat, e.g.
    "127.0.0.1" instead of "localhost".

    """
    def __init__(self, address="127.0.0.1", port=50051, ssl_context=None,
                 threaded=True):
        self._address = address
        self._port = port
        self._ssl_context = ssl_context
        self._threaded = threaded
        self._thread = None
        self.timer = None

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
        Utility method to send a JSON-RPC request to the server.

        This will raise an error if the request fails with an error or if
        the server is unreachable.

        :param method: name of the RPC method to call.
        :param params: parameters of the RPC method to call.
        :param id: ID of the JSON-RPC request (default: 0).
        :type method: str
        :type params: list
        :type id: int
        :returns: JSON-RPC response
        :rtype: dict
        :raises: RuntimeError
        """
        return send_rpc_request(self.url, method, params, id)

    def start(self):
        """
        Start the server.

        This method is non-blocking, the RPC server will run on a separate
        daemon thread. This way it is not necessary to call :meth:`stop`
        before the main thread terminates.
        """
        # Handle a previous Thread.join() timeout.
        if self._thread and not self._thread.isAlive():
            self._thread = None

        # Return if the server thread is already running.
        elif self._thread:
            return

        def run():
            # Note: 'threaded' means that each request is handled using a
            # separate thread. This introduces some overhead costs.
            try:
                return run_simple(self._address, self._port, application,
                                  ssl_context=self._ssl_context,
                                  threaded=self._threaded)
            except Exception as e:
                _log.exception("Exception caught on RPC server thread: %s"
                               % e)
                # Stop the engine timer for processing requests.
                self.timer.stop()
                self.timer = None

        self._thread = threading.Thread(target=run)
        self._thread.setDaemon(True)
        self._thread.start()

        def natlink_timer():
            # Let the server's thread run for a bit.
            if self._thread:
                self._thread.join(0.05)
                server_timer_function()

        # Create a timer with the current engine in order to process methods
        # properly. Have the timer run every second.
        engine = get_engine()
        if engine.name == "natlink":
            timer_function = natlink_timer
        else:
            timer_function = server_timer_function
        self.timer = engine.create_timer(timer_function, 1)

        # Wait a few milliseconds to allow the server to start properly.
        time.sleep(0.1)

    def stop(self):
        """
        Stop the server if it is running.
        """
        # Handle a previous Thread.join() timeout.
        if self._thread and not self._thread.isAlive():
            self._thread = None

        # Return if the server isn't currently running.
        if not self._thread:
            return

        # Stop the engine timer for processing requests.
        self.timer.stop()
        self.timer = None

        # werkzeug is normally stopped through a request to the server.
        self.send_request("shutdown_rpc_server", [])
        timeout = 5
        self._thread.join(timeout)
        if self._thread.isAlive():
            _log.warning("RPC server thread failed to stop after %d seconds"
                         % timeout)
        else:
            self._thread = None

    def add_method(self, name, method):
        """
        Add an RPC method to the server.

        Restarting the server is *not* required for the new method to be
        available.

        This can be used to override method implementations if that is
        desirable.

        :param name: the name of the RPC method to add.
        :param method: the implementation of the RPC method to add.
        :type name: str
        :type method: callable
        """
        dispatcher[name] = method

    def remove_method(self, name):
        """
        Remove an RPC method from the server. This will not raise an error
        if the method does not exist.

        Restarting the server is *not* required for the change to take
        effect.

        :param name: the name of the RPC method to remove.
        :type name: str
        """
        dispatcher.pop(name, None)

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
