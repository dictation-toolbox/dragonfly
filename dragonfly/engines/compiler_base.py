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
    This file implements the compiler base class.
"""


import dragonfly.log as log_
import dragonfly.grammar.elements as elements_


#---------------------------------------------------------------------------

class CompilerError(Exception):
    pass


#---------------------------------------------------------------------------

class CompilerBase(object):

    _log = log_.get_log("engine.compiler")

    element_compilers = [
        (elements_.Sequence,    lambda s,e,*a,**k: s._compile_sequence(e,*a,**k)),
        (elements_.Alternative, lambda s,e,*a,**k: s._compile_alternative(e,*a,**k)),
        (elements_.Optional,    lambda s,e,*a,**k: s._compile_optional(e,*a,**k)),
        (elements_.Literal,     lambda s,e,*a,**k: s._compile_literal(e,*a,**k)),
        (elements_.RuleRef,     lambda s,e,*a,**k: s._compile_rule_ref(e,*a,**k)),
        (elements_.ListRef,     lambda s,e,*a,**k: s._compile_list_ref(e,*a,**k)),
        (elements_.Dictation,   lambda s,e,*a,**k: s._compile_dictation(e,*a,**k)),
        (elements_.Impossible,  lambda s,e,*a,**k: s._compile_impossible(e,*a,**k)),
        ]

    #-----------------------------------------------------------------------

    def __str__(self):
        return "%s()" % self.__class__.__name__

    #-----------------------------------------------------------------------
    # Methods for compiling grammars.

    def compile_grammar(self, grammar, *args, **kwargs):
        raise NotImplementedError("Compiler %s not implemented." % self)

    #-----------------------------------------------------------------------
    # Methods for compiling elements.

    def compile_element(self, element, *args, **kwargs):
        # Look for a compiler method to handle the given element.
        for element_type, compiler in self.element_compilers:
            if isinstance(element, element_type):
                compiler(self, element, *args, **kwargs)
                return

        # Didn't find a compiler method for this element type.
        raise NotImplementedError("Compiler %s not implemented"
                                  " for element type %s."
                                  % (self, element))

    #-----------------------------------------------------------------------

    def _compile_unknown_element(self, element, *args, **kwargs):
        raise NotImplementedError("Compiler %s not implemented"
                                  " for element type %s."
                                  % (self, element))

    _compile_sequence     = _compile_unknown_element
    _compile_alternative  = _compile_unknown_element
    _compile_optional     = _compile_unknown_element
    _compile_literal      = _compile_unknown_element
    _compile_rule_ref     = _compile_unknown_element
    _compile_list_ref     = _compile_unknown_element
    _compile_dictation    = _compile_unknown_element
    _compile_impossible   = _compile_unknown_element
