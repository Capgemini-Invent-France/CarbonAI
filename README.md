# PyPowerGadget

This project aims at creating a python package that allows you to monitor the power consumption of any python function.

## Install

First of all you need to install the intel utility allowing you to monitor power consumption ([support](https://software.intel.com/en-us/articles/intel-power-gadget)):
* [Windows](https://software.intel.com/file/823776/download)
* [MacOS](https://software.intel.com/sites/default/files/managed/91/6b/Intel%20Power%20Gadget.dmg)
* Linux : no need of power gadgets ;)

To install this package, clone this repo and run `pip install .`


## Usage

To monitor the power consumption of a function, follow this example:
```python
from PyPowerGadget import PowerMeter
power_meter = PowerMeter()
result_of_your_function = power_meter.mesure_power(
    <your_function>,
    description="describe your function here"
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

|Datetime | ISO | Country | Total Elapsed CPU Time (sec) | Total Elapsed GPU Time (sec) | Cumulative Package Energy (mWh) | Cumulative IA Energy (mWh) | Cumulative GPU Energy (mWh) | Cumulative DRAM Energy (mWh) | PUE | CO2 emitted (gCO2e) | Description
|---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ----
|2020-02-26 16:56:00.032110 | FR | France | 10 | 0 | 56 | 42 | 0 | 2.2 | 1.3 | 0.0045 | Pytorch 1 epoch of a ResNet
|2020-02-26 16:58:48.482963 | FR | France | 8 | 0 | 50 | 39 | 0 | 1.6 | 1.3 | 0.0042 | Sklearn MLPClassifier; params=...; trained on the MNIST dataset

</div>

### Documentation
