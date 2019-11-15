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

"""
Mock module to allow dragonfly to be imported on linux locally.
Heavily modified to allow more dragonfly functionality to work
regardless of operating system.
"""

from .actions import ActionBase


class MockBase(object):
    def __init__(self, *args, **kwargs):
        pass


class MockAction(ActionBase):
    """ Mock class for dragonfly actions. """
    def __init__(self, *args, **kwargs):
        ActionBase.__init__(self)
