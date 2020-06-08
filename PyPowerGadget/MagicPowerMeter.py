__all__ = ["MagicPowerMeter"]

from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring

import PyPowerGadget.PowerMeter


@magics_class
class MagicPowerMeter(Magics):
    def __init__(self, shell):
        super(MagicPowerMeter, self).__init__(shell)

    @magic_arguments()
    @argument("--data_type", help="Type of data used")
    @argument("--data_shape", help="Size of the data used")
    @argument("--algorithm_params", help="Some informative parameters used")
    @argument("--comments", type=str, help="Comments to describe what is done")
    @argument("power_meter", help="The name of the package used here")
    @argument("package", type=str, help="The name of the package used here")
    @argument("algorithm", type=str, help="The algorithm type used here")
    @cell_magic
    def mesure_power(self, line, cell):
        options = parse_argstring(self.mesure_power, line)
        if options.power_meter not in self.shell.user_ns.keys():
            raise NameError("The PowerMeter variable passed is not referenced")
        self.power_meter = self.shell.user_ns[options.power_meter]
        if not isinstance(self.power_meter, PyPowerGadget.PowerMeter):
            raise TypeError("The first argument is not a PowerMeter object")
        options = vars(options)
        del options["power_meter"]
        with self.power_meter(**options) as p_m:
            self.shell.run_cell(cell)
            print("done")


def load_ipython_extension(ipython):
    ipython.register_magics(MagicPowerMeter)
