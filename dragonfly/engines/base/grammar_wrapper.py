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
GrammarWrapperBase class
============================================================================

"""

try:
    from inspect import getfullargspec as getargspec
except ImportError:
    # Fallback on the deprecated function.
    from inspect import getargspec


class GrammarWrapperBase(object):

    def __init__(self, grammar, engine, recobs_manager):
        self.grammar = grammar
        self.engine = engine
        self.recobs_manager = recobs_manager

    def _process_grammar_callback(self, func, **kwargs):
        if not func:
            return

        # Only send keyword arguments that the given function accepts.
        argspec = getargspec(func)
        arg_names, kwargs_names = argspec[0], argspec[2]
        if not kwargs_names:
            kwargs = { k: v for (k, v) in kwargs.items() if k in arg_names }

        return func(**kwargs)
