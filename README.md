# PyPowerGadget

This project aims at creating a python package that allows you to monitor the power consumption of any python function.

## Install

First of all you need to install the intel utility allowing you to monitor power consumption ([support](https://software.intel.com/en-us/articles/intel-power-gadget)):
* [Windows](https://software.intel.com/file/823776/download)
* [MacOS](https://software.intel.com/sites/default/files/managed/91/6b/Intel%20Power%20Gadget.dmg)
* Linux, no need to install any software, but on some installations the program need to be run as root

To install this package :
```
git clone https://gitlab.com/martinChauvin/green-ai.git
cd green-ai
python setup.py install
pip install .
```

## Disclaimer
This package collects personal data.
By using it, you agree to the collection of :
* your username
* your country
* the name of your project
* your computer's power consumption
* the information you provided

## Usage
*On linux you need to run python as root : `sudo python3 main.py` and sometimes you will also have to add other info `sudo PYTHONUSERBASE=/home/ec2-user/.local python3 main.py`*

There are several ways to use this package depending on how you develop.
You just have to import the `PowerMeter` object, initialise it and call the function you want to monitor.
Please insert a description of the running function, the dataset, the model, any info would be useful.

### Function decorator
To monitor the power consumption of a function, follow this example:
```python
from PyPowerGadget import PowerMeter
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

### Jupyter notebook magic function
To monitor the power consumption of a jupyter notebook cell, follow this example:
```jupyter
%load_ext PyPowerGadget.MagicPowerMeter
from PyPowerGadget import PowerMeter
power_meter = PowerMeter(project_name="MNIST classifier")

-----------------

%%measure_power power_meter "package_name_used" "algorithm" --data_type "tabular" --data_shape "your_data_shape" --algorithm_params "n_estimators=300, max_depth=15" --comments "Classifier trained on the MNIST dataset, 3rd test"
Do somthing

```

### Inline code
To monitor the power consumption of some specific inline code, there are 2 ways:

**Using the with statement**

This is the prefered method as it will stop the process even if you get an error
```python
from PyPowerGadget import PowerMeter
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

**Using the *start and stop method***

This method won't stop the process unless told to do so
```python
from PyPowerGadget import PowerMeter
power_meter = PowerMeter(project_name="MNIST classifier")

power_meter.start_measure(
  package="sklearn",
  algorithm="RandomForestClassifier",
  data_type="tabular",
  data_shape=<your_data>.shape,
  algorithm_params="n_estimators=300, max_depth=15",
  comments="Classifier trained on the MNIST dataset, 3rd test"
)
# Do something
power_meter.stop_measure()
```


### Documentation

*class* **PyPowerGadget.PowerMeter**(*project_name="", user_name="", cpu_power_log_path="", get_country=True*)
&nbsp;&nbsp;&nbsp;&nbsp;PowerMeter is a general tool to monitor and log the power consumption of any given function.
>project_name (optional) : str

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;The name of the project you are working on (for logging purpose)

>user_name (optional) : str

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;The name of the user using the tool (for logging purpose)
>cpu_power_log_path (optional) : str

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;The path to the tool "PowerLog"
>get_country (optional) : bool

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Whether use user country location or not
<hr/>

> &nbsp;&nbsp;&nbsp;&nbsp;**measure_power**(*func, package, algorithm, data_type="tabular", data_shape="", algorithm_params="", comments=""*)

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;measure the power consumption of any given function

> &nbsp;&nbsp;&nbsp;&nbsp;func : python function

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;The python function that will be monitored

> &nbsp;&nbsp;&nbsp;&nbsp;package : str

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;A string describing the package used by this function (e.g. sklearn, Pytorch, ...)
> &nbsp;&nbsp;&nbsp;&nbsp;algorithm : str

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;A string describing the algorithm used in the function monitored (e.g. RandomForestClassifier, ResNet121, ...)

> &nbsp;&nbsp;&nbsp;&nbsp;data_type : str (among : tabular, image, text, time series, other)

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;A string describing the type of data used for training

> &nbsp;&nbsp;&nbsp;&nbsp;data_shape : str or tuple

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;A string or tuple describing the quantity of data used

> &nbsp;&nbsp;&nbsp;&nbsp;algorithm_params (optional) : str

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;A string describing the parameters used by the algorithm
> &nbsp;&nbsp;&nbsp;&nbsp;comments (optional) : str

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;A string to provide any useful information

&nbsp;&nbsp;&nbsp;&nbsp; This method returns the result of the provided function and log collected data
