"""
Wrapper of the Python class PowerMeter for a notebook usage
"""
__all__ = ["MagicPowerMeter"]

from IPython.core.magic import Magics, cell_magic, magics_class  # type: ignore
from IPython.core.magic_arguments import (  # type: ignore
    argument,
    magic_arguments,
    parse_argstring,
)

from .power_meter import PowerMeter


@magics_class
class MagicPowerMeter(Magics):
    """
    This class will be used to use a PowerMeter instance in a notebook cell.

    This class aims at allowing the usage of ipython magic functions.
    It is not made to be used alone

    Parameters
    ----------
    Magics : IPythonShell
        An ipython shell

    See Also
    --------
    MagicPowerMeter.measure_power : Measure the power consumption using a \
        ipython magic function
    PowerMeter : Instanciate a PowerMeter

    Examples
    --------

    Load the ``MagicPowerMeter`` extension then declare a PowerMeter as usual

    .. code-block:: python

        %load_ext carbonai.MagicPowerMeter
        from carbonai import PowerMeter
        power_meter = PowerMeter(project_name="MNIST classifier", \
            is_online=False, location="FR")

    """

    def __init__(self, shell):
        super().__init__(shell)
        self.power_meter = None

    @magic_arguments()
    @argument("power_meter", help="The PowerMeter object of this project")
    @argument("package", type=str, help="The name of the package used here")
    @argument("algorithm", type=str, help="The algorithm type used here")
    @argument("--step", type=str, help="Type of data used")
    @argument("--data_type", help="Type of data used")
    @argument("--data_shape", help="Shape of the data used")
    @argument(
        "--algorithm_params",
        help="Some informative parameters \
            used in your algorithm",
    )
    @argument("--comments", type=str, help="Comments to describe what is done")
    @cell_magic
    def measure_power(self, line, cell):
        """
        An IPython magic function to measure the power consumption of \
        a given cell

        Parameters
        ----------
        power_meter : carbonai.PowerMeter
            A PowerMeter object used to collect the carbon logs
        package : str
            A string describing the package used by this function \
                (e.g. sklearn, Pytorch, ...)
        algorithm : str
            A string describing the algorithm used in the function \
                monitored (e.g. RandomForestClassifier, \
                ResNet121, ...)
        step : {'inference', 'training', 'other', 'test', \
            'run', 'preprocessing'}, optional
            A string to provide useful information on the current stage of \
                the alogrithm
        data_type : \
            {'tabular', 'image', 'text', 'time series', 'other'}, optional
            A string describing the type of data used for training
        data_shape : str or tuple, optional
            A string or tuple describing the quantity of data used
        algorithm_params : str, optional
            A string describing the parameters used by the algorithm
        comments : str, optional
            A string to provide any useful information

        Returns
        -------

        See also
        --------
        MagicPowerMeter : Loads the jupyter carbonai extension
        PowerMeter : Instantiate a PowerMeter
        PowerMeter.measure_power : Another way to measure the power \
            usage of some code

        Examples
        --------
        Load the ``MagicPowerMeter`` extension then declare a PowerMeter \
            as usual

        .. code-block:: python

            %load_ext carbonai.MagicPowerMeter
            from carbonai import PowerMeter
            power_meter = PowerMeter(project_name="MNIST classifier", \
                is_online=False, location="FR")

        In each cell you want to measure, you can then use the \
            ``measure_power`` cell magic

        .. code-block:: python

            %%measure_power power_meter "package_name_used" \
                "algorithm" --step "training" --data_type "tabular" \
                --data_shape "your_data_shape" \
                --algorithm_params "n_estimators=300, max_depth=15" \
                --comments "Classifier trained on the MNIST dataset, 3rd test"
            # Do something

        """
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
