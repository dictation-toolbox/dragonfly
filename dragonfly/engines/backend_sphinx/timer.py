#
# This file is part of Dragonfly.
# (c) Copyright 2017-2022 by Dane Finlay
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
Multiplexing interface for the CMU Pocket Sphinx engine
============================================================================

"""

from dragonfly.engines.base import DelegateTimerManager


class SphinxTimerManager(DelegateTimerManager):
    """
        Timer manager for the CMU Pocket Sphinx engine.

        This class allows running timer functions if the engine is
        currently processing audio via one of three engine processing
        methods:

         - :meth:`process_buffer`
         - :meth:`process_wave_file`
         - :meth:`do_recognition`

        .. note ::

           Long-running timers will block Dragonfly from processing what
           was said, so be careful how you use them!

           Audio frames will not normally be dropped because of timers,
           long-running or otherwise.

    """
