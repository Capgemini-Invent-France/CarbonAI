.. _examples:

========
Examples
========

There are several ways to use this package depending on how you develop.
You just have to import the `PowerMeter` object, initialise it and call the function you want to monitor.
Please provide a description of the running function, the dataset, the model, or any info you deem useful.

In most cases, you only have to declare a ``PowerMeter`` once per file/project.

Easy information filling 
-------------------------

To avoid filling information regarding the project at each instanciation,
it is possible to use a configuration file to do it only once:

.. code-block:: JSON

    {
        "project_name": "Project X",
        "program_name": "Program X",
        "client_name": "Client X",
        "cpu_power_log_path": "",
        "get_country": true,
        "is_online": false,
        "user_name": "customUsername",
        "filepath": "",
        "api_endpoint": "...", 
        "location":"FR"
    }

The JSON-formatted file is then handled by the method **PowerMeter.from_config** where an absolute path must be given.



.. code-block:: python

    from CarbonAImpact import PowerMeter
    PROJECT_PATH = ".../path-to-the-config.json"
    power_meter = PowerMeter.from_config(PROJECT_PATH)


Function decorator
------------------

To monitor the power consumption of a function, follow this example:

.. code-block:: python

    from CarbonAImpact import PowerMeter
    power_meter = PowerMeter(project_name="MNIST classifier", is_online=False, location="FR")

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

Jupyter notebook magic function
-------------------------------
To monitor the power consumption of a jupyter notebook cell, follow this example:

.. code-block:: python

    %load_ext CarbonAImpact.MagicPowerMeter
    from CarbonAImpact import PowerMeter
    power_meter = PowerMeter(project_name="MNIST classifier", is_online=False, location="FR")

.. code-block:: python

    %%measure_power power_meter "package_name_used" "algorithm" --data_type "tabular" --data_shape "your_data_shape" --algorithm_params "n_estimators=300, max_depth=15" --comments "Classifier trained on the MNIST dataset, 3rd test"
    # Do something

``with`` statement
------------------------
This is the prefered inline method as it will stop the process even if you get an error

.. code-block:: python

    from CarbonAImpact import PowerMeter
    power_meter = PowerMeter(project_name="MNIST classifier", is_online=False, location="FR")

    with power_meter(
        package="sklearn",
        algorithm="RandomForestClassifier",
        data_type="tabular",
        data_shape=<your_data>.shape,
        algorithm_params="n_estimators=300, max_depth=15",
        comments="Classifier trained on the MNIST dataset, 3rd test"
    ):
        # Do something


Start and stop method
-------------------------------

This method won't stop the monitoring process unless told to do so, and therefore is not recommended

.. code-block:: python

    from CarbonAImpact import PowerMeter
    power_meter = PowerMeter(project_name="MNIST classifier", is_online=False, location="FR")

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
