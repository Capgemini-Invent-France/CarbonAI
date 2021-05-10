   
=========================================
Welcome to CarbonAImpact's documentation!
=========================================

This project aims at creating a python package that allows you to monitor the power consumption and CO2 emissions of any python function.

Getting Started
===============

See the :ref:`installation` page to learn more details on how to install the package on your platform.
In most cases, it's as simple as 
``pip install git+https://gitlab.com/the_insighters/projects/carbonaimpact.git``

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

Green AI
========

With this package, we try to raise developers' awareness of the AI's carbon footprint. 

To get more details on green AI, see :ref:`about`. 
If you still have more questions or want to get in touch, :ref:`contact` us.


.. toctree::
   :maxdepth: 2
   :hidden:

   getting_started/index
   about/index
   reference/index
   contact

Notes
=====

.. warning::

   This package may log private data (username, country, project_name). If you do not provide
   any api_endpoint, we will never have access to this data.

   On the other hand, if you chose to share your data with us (by using our endpoint:
   https://ngji0jx9dc.execute-api.eu-west-3.amazonaws.com/post_new_item ), we commit to anonymize
   any data shared.
