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
Example dragonfly RPC client.

This requires the 'requests' Python package.
"""

import json
import requests


def main():
    # Send a 'list_grammars' request to the server and print the response.
    # This is roughly what the 'dragonfly.rpc.util.send_rpc_request'
    # function does.
    url = "http://127.0.0.1:50051/jsonrpc"
    headers = {'content-type': 'application/json'}
    payload = {
        # Method to call.
        "method": "list_grammars",

        # Method parameters containing the server's security token.
        # Change the placeholder value to the security token normally
        # generated and printed when the RPC server is initialised.
        "params": {"security_token": "<security-token>"},
        # "params": ["<security-token>"],

        # Protocol version and request ID.
        "jsonrpc": "2.0",
        "id": 0,
    }
    response = requests.post(
        url, data=json.dumps(payload), headers=headers
    ).json()

    # Print the names of loaded grammars and rules.
    for grammar in response["result"]:
        rules = grammar["rules"]
        print("Grammar '%s' (%d rules)" % (grammar["name"], len(rules)))
        for rule in rules:
            print("Rule '%s'" % grammar["name"])


if __name__ == '__main__':
    main()
