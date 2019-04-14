from ..base.integer_internal  import (MapIntBuilder, CollectionIntBuilder,
                                      MagnitudeIntBuilder, IntegerContentBase)
from .number import int_0, int_1_9, int_10_19, int_20_90_10

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

#---------------------------------------------------------------------------

class LineIntegerContent(IntegerContentBase):
    builders = [int_0, int_1_9, int_10_19, int_20_99, int_10_99,
                int_x01_x99, int_x10_x99, int_x000_x099, int_x100_x999]
