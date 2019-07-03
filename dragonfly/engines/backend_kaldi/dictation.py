﻿#
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
Dictation container for the Kaldi engine.

"""

import logging, locale

from six import PY2

from ...grammar.elements_basic import Dictation as BaseDictation

#---------------------------------------------------------------------------
# Cloud dictation classes -- elements capable of local or cloud dictation.

class CloudDictation(BaseDictation):

    cloud_default = True

    def __init__(self, *args, **kwargs):
        self.cloud = kwargs.pop('cloud', self.cloud_default)
        BaseDictation.__init__(self, *args, **kwargs)

class LocalDictation(BaseDictation):

    cloud_default = False

    def __init__(self, *args, **kwargs):
        self.cloud = kwargs.pop('cloud', self.cloud_default)
        BaseDictation.__init__(self, *args, **kwargs)
