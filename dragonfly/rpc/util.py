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
RPC utility functions
----------------------------------------------------------------------------
"""

import json
import requests


def send_rpc_request(url, method, params, id=0):
    """
    Utility function to send a JSON-RPC request to a server.

    This will raise an error if the request fails with an error or if
    the server is unreachable.

    :param url: the URL to send the JSON-RPC request to.
    :param method: name of the RPC method to call.
    :param params: parameters of the RPC method to call.
    :param id: ID of the JSON-RPC request (default: 0).
    :type url: str
    :type method: str
    :type params: list
    :type id: int
    :returns: JSON-RPC response
    :rtype: dict
    :raises: RuntimeError
    """
    headers = {'content-type': 'application/json'}
    payload = {
        "method": method,
        "params": params,
        "jsonrpc": "2.0",
        "id": id,
    }
    response = requests.post(
        url, data=json.dumps(payload), headers=headers
    ).json()

    # Handle an error in the response.
    error_info = response.get("error")
    if error_info:
        raise RuntimeError(
            "error calling RPC server method %s: %d, %s" %
            (method, error_info["code"], error_info["message"])
        )

    # Otherwise return the response.
    return response
