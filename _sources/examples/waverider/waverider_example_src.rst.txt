**Waverider source documentation** 
================================


1. import modules 
------------------

.. code-block:: python

    from Licel import  licel_tcpip, licel_wind, licel_netCDF
    import argparse
    import time
    import numpy as np


* **Licel**:  
    * **licel_tcpip**: module required for the communication with the ethernet controller.
    * **licel_wind** : module required for communicating with the waverider. 
    * **licel_netCDF**: module required for saving wind data to the netcdf format. 
    * **argparse**: module required for parsing the argument from command shell. 
    * **time**: module required for acquiring pc time.  
    * **numpy**: module required for holding data in numpy array as well as making datatype transformation  


2. Initialize acquisition parameters
------------------------------------------------

.. code-block:: python 

    #initialize acquisition parameters using parameters passed from command line interface
    myArguments = commandLineInterface()
    ip = myArguments.ip
    port = myArguments.port
    shots = myArguments.shots
    FFT_Size = myArguments.fft_size
    MaxRange_meter = myArguments.range 

3. Create object needed for data acquisition
----------------------------------------------

the following are wrapper for low level interaction with the hardware.

.. code-block:: python 

    ethernetController = licel_tcpip.EthernetController (ip, port)
    waverider = licel_wind.Waverider(ethernetController)
    ConfigInfo = licel_Config.Config("Acquis.ini")

* **ethernetController**: is the class responsible for handling the communication with the hardware.

* **waverider**: class holding method for setting specific waverider parameters.


4. initiate communication with the waverider 
---------------------------------------------------------------------------------
.. code-block:: python 

    ethernetController.openConnection()

* **ethernetController.openConnection()**: establishes connection with the controller
                                       on command port (default 2055) 

5. Configure the waverider hardware and get hardware specific information
---------------------------------------------------------------------------------------------------------
.. code-block:: python 

    print(waverider.getCAP())
    print(waverider.getID())
    print(waverider.getHWDescr())

    print(waverider.setShots(shots))
    print(waverider.getShotsSettings())

    print(waverider.setFFTsize(FFT_Size))
    print(waverider.getFFTsize())


* **waverider.getCAP()** : get the hardware capabilities.  
* **waverider.getID()**  : get the firmware version 
* **waverider.getHWDescr()**: get the hardware revision. 
* **waverider.setShots(shots)**: Set the number of shots we want to acquire. 
* **waverider.getShotsSettings()** : get the number of shots setting. 
* **waverider.setFFTsize(FFT_Size)** : set the number of ADC samples that goes into computing a single fft
* **waverider.getFFTsize()** : get the number of ADC samples that goes into computing a single fft

6. Calculate the number of fft that needs to be computed, depending on the distance range
---------------------------------------------------------------------------------------------------------
.. code-block:: python 

    numFFT = waverider.getRangebins(MaxRange_meter,FFT_Size, samplingRate_hz)

* **waverider.getRangebins(MaxRange_meter,FFT_Size, samplingRate_hz)** : Calculate the number of fft that needs to be computed,in order to acquire data up until the specified distance range. 
this will internally calculate the timingresolution for a signle fft, and the lidar range resolution.

The timing resolution = sampling period X fftsize 

lidar range resolution = timeResolution X (light_speed / 2)

number of fft for a specified range = distance range / lidar Range Resolution


7. Set the number of fft that needs to be computed, depending on the distance range
---------------------------------------------------------------------------------------------------------
.. code-block:: python 

    print(waverider.setNumFFT(numFFT))
    print(waverider.getNumFFT())

* **waverider.setNumFFT(numFFT)** : set the number of fft that needs to be computed by the waverider. 
* **waverider.getNumFFT()** : get the number of fft that needs to be computed by the waverider. 

8. Create the NETCDF file wrapper and fille the metadata
---------------------------------------------------------------------------------------------------------
.. code-block:: python 

    waverider_NetCDF = licel_netCDF.Licel_Netcdf_Wrapper("Test.nc","w", "Waverider",
                                                     numFFT, FFT_Size, num_trig)
    
    waverider_NetCDF.fillGeoPositionInfo("Berlin", Latitude, Longitude,
                                     Altitude, azimuth, zenith )
    
    waverider_NetCDF.fillAcquisitionInfo(MaxRange_meter, samplingRate_hz,
                                         shots, FFT_Size, waverider )

* **licel_netCDF.Licel_Netcdf_Wrapper("filename.nc","w", "Waverider",numFFT, FFT_Size, num_trig)**: returns a Licel_Netcdf_Wrapper that will enables us to write data to a netcdf file. 
the input parameters are as follows: 
    a. **"filename.nc"**: file name we want to create/ write to 
    b. **access mode**: "w" for writing to a file.
    c. **"Waverider"**: the device we acquire data from. this will have an impact on the data structure of the netcdf file.
    d. **numFFT**: number of fft that are to be computed.
    e. **FFT_Size**: number of ADC sample that goes into computing a single fft.
    f. **num_trig**: the number of trigger, currently only single trigger is supported.

* **waverider_NetCDF.fillGeoPositionInfo("Berlin", Latitude, Longitude,Altitude, azimuth, zenith )**: write the geographical information in the netcdf file.

* **waverider_NetCDF.fillAcquisitionInfo(MaxRange_meter, samplingRate_hz,shots, FFT_Size, waverider )**: write acquisition information to netcdf file:
the input paramters are as follows:
    a. **MaxRange_meter**: maximum acquisition range in meters. 
    b. **samplingRate_hz**: sampling rate of the waverider in hertz.
    c. **shots**: the target number of shots.
    d. **FFT_Size**: number of ADC sample that goes into computing a single fft.
    e. **waverider**: the waverider object create before from **licel_wind.Waverider(ethernetController)**

8. write the waverider time and pc time to netcdf file
---------------------------------------------------------------------------------------------------------
.. code-block:: python 

    waverider_NetCDF.timestamp_start[:] = waverider.getMSEC()
    waverider_NetCDF.pc_time_start[:] = waverider_NetCDF.time_unix_to_epoch_1904()

* **waverider.getMSEC()**: get the waverider time in milliseconds.
* **waverider_NetCDF.timestamp_start[:] = waverider.getMSEC()**: write the waverider time to netcdf.
* **waverider_NetCDF.time_unix_to_epoch_1904()**: get the pc time and convert it to time since 1904 epoch. 
current system start counting time since 1970, to be compatible with the Licel netcdf viewer, the time in netcdf file is written since 1904 epoch 

9. Reading data from the waverider and saving them to netcdf file.
---------------------------------------------------------------------------------------------------------
.. code-block:: python 

    CYCLE = 0
    startCycle = 0
    while CYCLE < RUNS : 
        waverider.startAcq()
        dataAvailable = False 
        while dataAvailable == False: 
            dataAvailable = waverider.isDataAvailable() 
            time.sleep(1/1000) 

        timestamp, powerSpectra= waverider.getData(FFT_Size,numFFT)
        waverider_NetCDF.pc_time_read[:] = waverider_NetCDF.time_unix_to_epoch_1904()

        currentShots = waverider.getCurrentShots()

        waverider_NetCDF.saveNetcdf(CYCLE, powerSpectra, timestamp, currentShots)
        CYCLE = CYCLE + 1

* **waverider.startAcq()**: the waverider will start the data acquisition. 

* **waverider.isDataAvailable()**: asks the waverider is there any data to be read. 
data is avaialbe when the requested number of shots is reached. 

* **waverider.getData(FFT_Size,numFFT)**: get the data from the waverider. this will return 2 numpy arrays.
first numpy array contains a single element of type uint64 representing the data acquisition timestamp. 

the second numpyarray contains the powerSpectra data of type uint64. note that a single power spectra size is half of the fft size. 

single power spectra size = fft size / 2 

total data array size = power spectra size X number of fft to be computed 

* **waverider_NetCDF.pc_time_read[:] = waverider_NetCDF.time_unix_to_epoch_1904()**: write the current pc time, when data is read to the netcdf file. 

* **currentShots = waverider.getCurrentShots()**: get the shot number of the dataset we just acquired.

* **waverider_NetCDF.saveNetcdf(CYCLE, powerSpectra, timestamp, currentShots)**: save the powerSpectra data, timestamp, currentShots, and cycle to a netcdf file.
