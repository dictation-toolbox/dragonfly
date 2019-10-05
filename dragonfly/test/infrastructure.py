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
"""
from dragonfly import Context

# ==========================================================================


class TestError(Exception):
    pass


# ==========================================================================

class Unique(object):
    """ Token class representing a unique identity. """

    def __init__(self, name):
        self._name = name

    def __repr__(self):
        return self._name


RecognitionFailure = Unique("RecognitionFailure")


# ==========================================================================


class TestContext(Context):
    """ Simple context class used to test rule and grammar contexts. """
    def __init__(self, active):
        super(TestContext, self).__init__()
        self.active = active

    def matches(self, executable, title, handle):
        # Ignore the parameters and return self.active.
        return self.active
