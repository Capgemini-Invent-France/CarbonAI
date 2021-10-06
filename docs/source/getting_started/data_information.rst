.. _data-information:

================
Data information
================
The data collected thanks to the package usage is recorded in a csv file. 
If you didn't set a specific filepath, the file will, by default, be stored in the same folder as your script, under the name `emissions.csv`.

Quick look at the data
------------------------
You should get a new line (in the csv file) for every usage of the package.

.. list-table:: data columns details
    :widths: 25 50
    :header-rows: 1
    :class: table table-hover

    * - Column name
      - Description
    * - Datetime 
      - Datetime of the record generation
    * - Country 
      - Name of the country where the package was used (based on the IP or what the user set)
    * - Platform 
      - Name of the os you're using
    * - User ID 
      - Name of the user who used the package (as set by itself)
    * - ISO 
      - ISO code of the country where the package was used (based on the IP or what the user set)
    * - Project name 
      - Name of the project for which the package was used
    * - Program name 
      - Name of the program for which the package was used
    * - Company name 
      - Name of the company for which the package was used
    * - Total Elapsed CPU Time (sec) 
      - Total time of CPU usage (in seconds)
    * - Total Elapsed GPU Time (sec) 
      - Total time of CPU usage (in seconds)
    * - Cumulative Package Energy (mWh) 
      - Total energy, in milli Watt hour, used by the computer while the algorithm was running
    * - Cumulative IA Energy (mWh) 
      - Total energy, in milli Watt hour, used by the CPU while the algorithm was running
    * - Cumulative GPU Energy (mWh) 
      - Total energy, in milli Watt hour, used by the GPU while the algorithm was running
    * - Cumulative DRAM Energy (mWh) 
      - Total energy, in milli Watt hour, used by the memory while the algorithm was running
    * - Cumulative process CPU Energy (mWh)
      - Total energy, in milli Watt hour, used by the CPU for this **specific** task while the algorithm was running
    * - Cumulative process DRAM Energy (mWh)
      - Total energy, in milli Watt hour, used by the memory for this **specific** task while the algorithm was running
    * - PUE 
      - Also known as cooling factor, indicates the extra energy used to cool the system down while the algorithm is running
    * - CO2 emitted (gCO2e)
      - Amount of CO2 emitted by the algorithm's usage, in gram. This value depends on the country and the energy mix used by the country to produce electricity
    * - Package 
      - *Declarative value*, package used by the user in the project
    * - Algorithm 
      - *Declarative value*, name of the algorithm(s) used
    * - Algorithm's parameters 
      - *Declarative value*, parameters used for the algorithm
    * - Data type 
      - *Declarative value*, type of data used to train the algorithm
    * - Data shape 
      - *Declarative value*, size of the database used to train the algorithm
    * - Comment 
      - *Declarative value*, comments made by the user
