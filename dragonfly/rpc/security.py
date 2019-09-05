#
# This file is based on how Aenea handles and generates security tokens.
# The original copyright notice is reproduced below.
#
# This file is part of Aenea
#
# Aenea is free software: you can redistribute it and/or modify it under
# the terms of version 3 of the GNU Lesser General Public License as
# published by the Free Software Foundation.
#
# Aenea is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with Aenea.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (2014) Alex Roper
# Alex Roper <alex@aroper.net>

import base64
import os


def compare_security_token(expected, actual):
    if len(expected) != len(actual):
        return False
    result = 0
    for x, y in zip(expected, actual):
        result |= ord(x) ^ ord(y)
    return result == 0


def generate_security_token():
    return base64.b64encode(os.urandom(32)).decode()
