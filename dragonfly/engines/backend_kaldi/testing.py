#
# This file is part of Dragonfly.
# (c) Copyright 2019 by David Zurow
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
Utility & testing classes for Kaldi backend
"""

import time
from contextlib import contextmanager

debug_timer_enabled = True
_debug_timer_stack = []

@contextmanager
def debug_timer(log, desc, enabled=True, independent=False):
    start_time = time.time()
    if not independent: _debug_timer_stack.append(start_time)
    spent_time_func = lambda: time.time() - start_time
    yield spent_time_func
    start_time_adjusted = _debug_timer_stack.pop() if not independent else 0
    if enabled:
        if debug_timer_enabled:
            log("%s %d ms" % (desc, (time.time() - start_time_adjusted) * 1000))
        if _debug_timer_stack and not independent:
            _debug_timer_stack[-1] += spent_time_func()
