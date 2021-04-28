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

   installation
   examples
   data_information