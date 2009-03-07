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
This file implements the main language-dependent interface to number
classes.

"""


import sys
from .rule_base       import Rule
from .elements_basic  import RuleRef


#---------------------------------------------------------------------------
# Initialize the number classes to *None*, so that they can be
#  set to the appropriate language-dependent types later on.

Integer  = None
Digits   = None
Number   = None


#---------------------------------------------------------------------------
# Mapping of language tags to module names.  Each of the module names
#  should implement the *Integer* and *Digits* classes for the given
#  speaker language.

_language_map = {
                 "en": "dragonfly.grammar.number_en",
                 "nl": "dragonfly.grammar.number_nl",
                }


#---------------------------------------------------------------------------
# Wrapper classes for easily wrapping the number classes up in
#  an appropriate referenced rule.  This keeps the grammars more
#  smaller and more efficient if a single number instance is
#  referenced multiple times.

class RuleWrap(RuleRef):

    _next_id = 0

    def __init__(self, name, element):
        rule_name = "_%s_%02d" % (self.__class__.__name__, RuleWrap._next_id)
        RuleWrap._next_id += 1
        rule = Rule(name=rule_name, element=element)
        RuleRef.__init__(self, rule=rule, name=name)


class IntegerRef(RuleWrap):

    _element_type = None

    def __init__(self, name, min, max):
        element = self._element_type(None, min, max)
        RuleWrap.__init__(self, name, element)


class DigitsRef(RuleWrap):

    _element_type = None

    def __init__(self, name=None, min=1, max=12, as_int=True):
        element = self._element_type(name=None, min=min,
                                     max=max, as_int=as_int)
        RuleWrap.__init__(self, name, element)


class NumberRef(RuleWrap):

    _element_type = None

    def __init__(self, name=None, zero=False):
        element = self._element_type(None, zero=zero)
        RuleWrap.__init__(self, name, element)


#---------------------------------------------------------------------------
# Method for loading language-dependent number classes.

def load_language(language):

    # Lookup the module name for the given language.
    try:
        module_name = _language_map[language]
    except KeyError:
        raise GrammarError("Attempt to load unknown language: %r"
                           % language)

    # Attempt to import the language-dependent module.
    try:
        top_module = __import__(module_name)
        module = sys.modules[module_name]
    except ImportError, e:
        raise GrammarError("Failed to load number module %r for language %r"
                           % (module_name, language))

    # Make the newly imported language-dependent Integer and Digits
    #  classes available in this module's global namespace.
    global Integer;  Integer = module.Integer
    global Digits;   Digits  = module.Digits

    # Import and set up the Number class.
    from dragonfly.grammar.number_base import Number as _Number
    _Number._element_type = IntegerRef
    global Number; Number = _Number

    # Said that the reference classes.
    IntegerRef._element_type = Integer
    DigitsRef._element_type  = Digits
    NumberRef._element_type  = Number


#---------------------------------------------------------------------------
# Load number classes for current language.

try:
    import dragonfly.engines.engine as _engine
    load_language(_engine.get_engine().language)
except Exception, e:
    from dragonfly.log import get_log as _get_log
    _log =_get_log("")
    _log.error("Failed to load language-specific number module: %s" % e)
