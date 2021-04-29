.. CarbonAImpact documentation master file, created by
   sphinx-quickstart on Wed Oct 28 17:29:00 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to CarbonAImpact's documentation!
=========================================

This project aims at creating a python package that allows you to monitor the power consumption and CO2 emissions of any python function.

Getting Started
===============

See the :ref:`installation` page to learn more on how to install the package on your computer

Here is an example of usage :

.. code-block:: python

   from CarbonAImpact import PowerMeter
   power_meter = PowerMeter(project_name="MNIST classifier")

   @power_meter.measure_power(
      package="sklearn",
      algorithm="RandomForestClassifier",
      data_type="tabular",
      data_shape=your_data.shape,
      algorithm_params="n_estimators=300, max_depth=15",
      comments="Classifier trained on the MNIST dataset, 3rd test"
   )
   def my_func(arg1, arg2, ...):
      # Do something

For more examples, check the :ref:`examples` page

For more information on how to use the package, check the :ref:`reference`.
For more information on the data collected, check the :ref:`data-information`.

.. toctree::
   :maxdepth: 2
   :hidden:

   getting_started/index
   about/index
   reference/index


Disclaimer
==========
This package collects personal data.
By using it, you agree to the collection of :

- your username (it will then be anonymized)
- your country
- the name of your project (as provided by yourself)
- your computer's power consumption
- the information you provided

