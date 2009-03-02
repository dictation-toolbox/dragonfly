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
    This file lists all of the basic grammar element classes.

    It is this file which is usually imported by end-user code which
    needs to use dragonfly grammar elements.
"""


import dragonfly.grammar.elements_basic as basic_
import dragonfly.grammar.elements_compound as compound_


#===========================================================================
# Element classes.

#---------------------------------------------------------------------------
# Element base class.

ElementBase     = basic_.ElementBase


#---------------------------------------------------------------------------
# Basic element classes.

Sequence        = basic_.Sequence
Alternative     = basic_.Alternative
Optional        = basic_.Optional
Repetition      = basic_.Repetition
Literal         = basic_.Literal
RuleRef         = basic_.RuleRef
Rule            = basic_.RuleRef        # For backwards compatibility.
ListRef         = basic_.ListRef
List            = basic_.ListRef        # For backwards compatibility.
DictListRef     = basic_.DictListRef
DictList        = basic_.DictListRef    # For backwards compatibility.
Empty           = basic_.Empty
Dictation       = basic_.Dictation
Impossible      = basic_.Impossible


#---------------------------------------------------------------------------
# Compound element classes.

Compound        = compound_.Compound
Choice          = compound_.Choice
