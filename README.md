# CarbonAI

This project aims at creating a python package that allows you to monitor the power consumption of any python function.

## Documentation

The complete documentation is available [here](https://capgemini-invent-france.github.io/CarbonAI/).

## Getting started
### Install

First of all you need to install the intel utility allowing you to monitor power consumption ([support](https://software.intel.com/en-us/articles/intel-power-gadget)):
* [Windows](https://software.intel.com/file/823776/download)
* [MacOS](https://software.intel.com/sites/default/files/managed/91/6b/Intel%20Power%20Gadget.dmg)
* Linux, no need to install any software

To install this package :
```sh
pip install carbonai
```

### Example

There are several ways to use this package depending on how you develop.
You just have to import the `PowerMeter` object, initialize it and call the function you want to monitor.
Please insert a description of the running function, the dataset, the model, any info would be useful.

#### Function decorator
To monitor the power consumption of a function, follow this example:
```python
from carbonai import PowerMeter
power_meter = PowerMeter(project_name="MNIST classifier")

@power_meter.measure_power(
  package="sklearn",
  algorithm="RandomForestClassifier",
  data_type="tabular",
  data_shape=<your_data>.shape,
  algorithm_params="n_estimators=300, max_depth=15",
  comments="Classifier trained on the MNIST dataset, 3rd test"
)
def my_func(arg1, arg2, ...):
  # Do something
```

#### Using the with statement
To monitor the power consumption of some specific inline code, you can use with statements

```python
from carbonai import PowerMeter
power_meter = PowerMeter(project_name="MNIST classifier")

with power_meter(
  package="sklearn",
  algorithm="RandomForestClassifier",
  data_type="tabular",
  data_shape=<your_data>.shape,
  algorithm_params="n_estimators=300, max_depth=15",
  comments="Classifier trained on the MNIST dataset, 3rd test"
):
  # Do something
```

## Contribute

All contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome.

You can find details on how to contribute in [our guide](CONTRIBUTING.md)
