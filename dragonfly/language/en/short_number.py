
'''
ShortIntegerRef
============================================================================

:class:`ShortIntegerRef` is a modified version of :class:`IntegerRef` which allows for greater flexibility in the way that numbers may be pronounced, allowing for words like "hundred" to be dropped. This may be particularly useful when navigating files by line or page number.

Some examples of allowed pronunciations:

================================     ======
Pronunciation                        Result
================================     ======
one                                   1
ten                                   10
twenty three                          23
two three                             23
seventy                               70
seven zero                            70
hundred                               100
one oh three                          103
hundred three                         103
one twenty seven                      127
one two seven                         127
one hundred twenty seven              127
seven hundred                         700
thousand                              1000
seventeen hundred                     1700
seventeen hundred fifty three         1753
seventeen fifty three                 1753
one seven five three                  1753
seventeen five three                  1753
four thousand                         4000
================================     ======

The class works in the same way as :class:`IntegerRef`, by adding the following as an extra.

.. code:: python

   ShortIntegerRef("name", 0, 1000),
'''

from ..base.integer_internal  import (MapIntBuilder, CollectionIntBuilder,
                                      MagnitudeIntBuilder, IntegerContentBase)
from .number import int_0, int_1_9, int_10_19, int_and_1_99, int_20_90_10, int_100s, int_1000000s

# Twenty five
int_20_99       = MagnitudeIntBuilder(
                   factor      = 10,
                   spec        = "<multiplier> [<remainder>]",
                   multipliers = [int_20_90_10],
                   remainders  = [int_1_9],
                  )
# Two five / seven zero
int_10_99       = MagnitudeIntBuilder(
                   factor      = 10,
                   spec        = "<multiplier> <remainder>",
                   multipliers = [int_1_9],
                   remainders  = [int_0, int_1_9],
                  )
# Oh five
int_and_1_9    = CollectionIntBuilder(
                   spec        = "(oh | zero) <element>",
                   set         = [int_1_9],
                  )
# Fifty five / five five
int_and_10_99    = CollectionIntBuilder(
                   spec        = "[and] <element>",
                   set         = [int_10_19, int_20_99, int_10_99],
                  )
# Hundred fifty / two hundred / four hundred seventy nine
int_x01_x99        = MagnitudeIntBuilder(
                   factor      = 100,
                   spec        = "[<multiplier>] hundred [<remainder>]",
                   multipliers = [int_1_9, int_10_19, int_20_99],
                   remainders  = [int_1_9, int_and_10_99],
                  )
# One oh nine / five fifty / one two five
int_x10_x99        = MagnitudeIntBuilder(
                   factor      = 100,
                   spec        = "<multiplier> [hundred] <remainder>",
                   multipliers = [int_1_9, int_10_19, int_20_99],
                   remainders  = [int_and_1_9, int_and_10_99],
                  )
# One thousand fifty
int_x000_x099       = MagnitudeIntBuilder(
                   factor      = 1000,
                   spec        = "[<multiplier>] thousand [<remainder>]",
                   multipliers = [int_1_9],
                   remainders  = [int_1_9, int_and_10_99]
                  )
# One thousand five fifty / one five fifty / one five five zero
int_x100_x999       = MagnitudeIntBuilder(
                   factor      = 1000,
                   spec        = "<multiplier> [thousand] <remainder>",
                   multipliers = [int_1_9],
                   remainders  = [int_x01_x99, int_x10_x99]
                  )

# Very similar to the one from number.py, but without int_1_9 multipliers
# as these are handled above.
int_1000s       = MagnitudeIntBuilder(
                   factor      = 1000,
                   spec        = "[<multiplier>] thousand [<remainder>]",
                   multipliers = [int_10_19, int_20_99, int_100s],
                   remainders  = [int_and_1_99, int_100s]
                  )
#---------------------------------------------------------------------------

class ShortIntegerContent(IntegerContentBase):
    builders = [int_0, int_1_9, int_10_19, int_20_99, int_10_99,
                int_x01_x99, int_x10_x99, int_x000_x099, int_x100_x999,
                int_1000s, int_1000000s]
