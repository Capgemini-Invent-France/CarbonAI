# PyPowerGadget

This project aims at creating a python package that allows you to monitor the power consumption of any python function.

## Install

First of all you need to install the intel utility allowing you to monitor power consumption ([support](https://software.intel.com/en-us/articles/intel-power-gadget)):
* [Windows](https://software.intel.com/file/823776/download)
* [MacOS](https://software.intel.com/sites/default/files/managed/91/6b/Intel%20Power%20Gadget.dmg)
* Linux, no need to install any software, but the program need to be run as root

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

*On linux you need to run python as root : `sudo python3 main.py`*

To monitor the power consumption of a function, follow this example:
```python
from PyPowerGadget import PowerMeter
power_meter = PowerMeter(project_name="MNIST classifier")
<result_of_your_function> = power_meter.mesure_power(
    <your_function>,
    package="sklearn",
    algorithm="RandomForestClassifier",
    data_type="tabular",
    data_shape=<your_data>.shape
    algorithm_params="n_estimators=300, max_depth=15",
    comments="Classifier trained on the MNIST dataset, 3rd test"
)(<your_function_arguments>)
```


You just have to import the `PowerMeter` object, initialise it and call the function you want to monitor.
Please insert a description of the running function, the dataset, the model, any info would be useful.

Energy usage, CO2 emissions and  other useful stats are logged in a file. You can access this file with the following function:
```python
import PyPowerGadget
logged_data = PyPowerGadget.get_logged_data()
logged_data
```
<div style="font-size:8pt;">

|Datetime                  |User ID      |ISO|Country|Platform|Project name|Total Elapsed CPU Time (sec)|Total Elapsed GPU Time (sec)|Cumulative Package Energy (mWh)|Cumulative IA Energy (mWh)|Cumulative GPU Energy (mWh)|Cumulative DRAM Energy (mWh)|PUE|CO2 emitted (gCO2e)  |Package|Algorithm     |Algorithm's parameters|Data type|Data shape|Comment|
|--------------------------|-------------|---|-------|--------|------------|----------------------------|----------------------------|-------------------------------|--------------------------|---------------------------|----------------------------|---|---------------------|-------|--------------|----------------------|---------|----------|-------|
|2020-03-04 17:53:36.289029|martinchauvin|FR |France |darwin  |green_ai    |10.087129                   |0                           |23.081851            |10.375519                 |0                          |2.296532                    |1.3|0.0013     |Sklearn   |MLPClassifier|hidden_layers=(200;)|tabular  |(7000, 64)   |Toy training on the MNIST dataset |
|2020-03-04 17:54:29.610171|martinchauvin|FR |France |darwin  |green_ai    |10.09472         |0                           |27.315876            |13.769294                 |0                          |2.562374                    |1.3|0.001679385|Pytorch   |ResNet121| layers=(Conv(3x3), BatchNorm,...)                     |images  |(7000, 64)  |3rd training|

</div>

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

> &nbsp;&nbsp;&nbsp;&nbsp;**mesure_power**(*func, package, algorithm, data_type="tabular", data_shape="", algorithm_params="", comments=""*)

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mesure the power consumption of any given function

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
