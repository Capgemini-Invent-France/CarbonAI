"""
Wrapper of the Python class PowerMeter for a notebook usage
"""
__all__ = ["MagicPowerMeter"]

from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring

from . import PowerMeter


@magics_class
class MagicPowerMeter(Magics):
    """
    This class will be used to use a PowerMeter instance
    in a notebook cell.
    """
    def __init__(self, shell):
        super().__init__(shell)

    @magic_arguments()
    @argument("--data_type", help="Type of data used")
    @argument("--data_shape", help="Size of the data used")
    @argument("--algorithm_params", help="Some informative parameters used in your algorithm")
    @argument("--comments", type=str, help="Comments to describe what is done")
    @argument("power_meter", help="The PowerMeter object of this project")
    @argument("package", type=str, help="The name of the package used here")
    @argument("algorithm", type=str, help="The algorithm type used here")
    @cell_magic
    def measure_power(self, line, cell):
        options = parse_argstring(self.measure_power, line)
        if options.power_meter not in self.shell.user_ns.keys():
            raise NameError("The PowerMeter variable passed is not referenced")
        self.power_meter = self.shell.user_ns[options.power_meter]
        if not isinstance(self.power_meter, PowerMeter):
            raise TypeError("The first argument is not a PowerMeter object")
        options = vars(options)
        del options["power_meter"]
        with self.power_meter(**options):
            self.shell.run_cell(cell)


def load_ipython_extension(ipython):
    ipython.register_magics(MagicPowerMeter)
