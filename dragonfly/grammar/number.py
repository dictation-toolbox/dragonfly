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
This file implements the main interface to number classes.
"""


from elements_basic import (RuleRef)


Integer = None
Digits = None
Number = None


def _ref(element):
    rule = Rule(rule_name, element=element)
    return RuleRef(ref_name, rule)


def load_language(language):
    try:
        module_name = language_map[language]
    except KeyError:
        raise GrammarError("Attempt to load unknown language: %r"
                           % language)

    try:
        module = __import__(module_name)
    except ImportError, e:
        raise GrammarError("Failed to load number module %r for language %r"
                           % (module_name, language))

    global Integer; Integer = module.Integer; IntegerRef = _ref(Integer)


# Load number classes for current language.
import dragonfly.engines.engine as _engine
load_language(_engine.get_engine().language)
