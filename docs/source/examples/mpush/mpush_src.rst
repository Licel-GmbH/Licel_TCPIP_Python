**mpush source documentation** 
================================

In what follow we will describe section by section the mpush example. 

1. import modules 
------------------
.. code-block:: python

    from Licel import licel_tcpip, licel_data, licel_Config
    from datetime import datetime
    import argparse 

* **Licel**:  
    * **licel_tcpip**: module required for the communication with the ethernet controller.
    * **licel_data** : module required for parsing and processing the raw data. 
    * **licel_Config**: module required for parsing the configuration file. 

* **argparse**: module required for parsing the argument from command shell. 
* **datetime**: module required for acquiring time. 


2. Initialize acquisition parameters
------------------------------------------------

.. code-block:: python 

    #initialize acquisition parameters using parameters passed from command line interface
    myArguments = commandLineInterface()
    ip = myArguments.ip
    port = myArguments.port
    desiredShots = myArguments.shots
    ACQUISTION_CYCLES = myArguments.acq
    ACQUISPERFILE = myArguments.acquis_per_file 
    LOGPUSHDATA = myArguments.log 

3. Create object needed for data acquisition
----------------------------------------------

the following are wrapper for low level interaction with the hardware.

.. code-block:: python 

    ethernetController = licel_tcpip.EthernetController (ip, port)
    dataParser = licel_data.DataParser()
    ConfigInfo = licel_Config.Config("Acquis.ini")


    
* **ethernetController**: is the class responsible for handling the communication with the hardware.

* **dataParser**: class holding method for parsing ``ethernetController.pushBuffer``.

* **ConfigInfo**: class holding method for reading and storing configuration from the ini file.
                  ini file must be passed as argument, in this example ``Acquis.ini``  

4. Read ConfigInfo and initiate communication with hardware 
----------------------------------------------------------------------------------


.. code-block:: python 

    ConfigInfo.readConfig()
    ethernetController.openConnection()
    ethernetController.openPushConnection()

* **ConfigInfo.readConfig()** : reads and stores the configuration parameter in ``ConfigInfo``
                            value can be accessed as specified in :ref:`Config-ref`

* **ethernetController.openConnection()**: establishes connection with the controller
                                       on command port (default 2055) 

* **ethernetController.openPushConnection()**: establishes connection with the controller
                                           on push port (command port +1)


6. Get installed transient recorders in the system
--------------------------------------------------------------------------------------------------------------------
.. code-block:: python 

    
    print(ethernetController.listInstalledTr())   

* **ethernetController.listInstalledTr()**: will attempt to communicate with Transient recorders ranging for (0 .. 7).
        and then return a dictionary describing if TR(n) is installed or not. 
        if no Transient recorder is detected in the system, it will raise an ``RuntimeError`` 


7. Configure the active transient records hardware in the system as specified in the configuration file
---------------------------------------------------------------------------------------------------------
.. code-block:: python 

     ethernetController.configureHardware(ConfigInfo)

* the current supported configuration is :
    * Discriminator level  
    * pretrigger 
    * Threshold 
    * frequency divider 
    * maximum number of shots 
    * input range 

for more information about the supported configuration see :ref:`TRini-File`

.. _Start Mpush:
8. Start the MPUSH acquisition.
-----------------------------------------------------------

.. code-block:: python 

    print(ethernetController.MPushStartFromConfig(desiredShots, ConfigInfo))


* **ethernetController.MPushStartFromConfig(desiredShots, ConfigInfo)**: 
    Starts the MPUSH acquisition mode from configuration: 
    
    The ethernet controller wil automatically transfer data via push socket as soon as data is available.

    Internally this function will: 
    
    * Get the timestamp endianness.
    * Get hardware information for each active transient recorder in Config.
    * Calculate the expected number of bytes to be received.
    * Generate the MPUSH command depending on the Config.  
    * Sends the generated MPUSH command to the controller. 

    timestamp endianness and Hardware information are to be stored in the ``ethernetController`` object
    internally to be later used when parsing and saving the data. 


9. Main acquisition loop
--------------------------

.. code-block:: python
    
    cycle_count = 0
    while ((cycle_count < ACQUISTION_CYCLES) or (ACQUISTION_CYCLES == -1) ):
        try:
            cycle_count += 1
            singleAcquistionCycle(ethernetController, dataParser, ConfigInfo)
        except (ConnectionError, ConnectionResetError, TimeoutError) as myExecption:
            cycle_count = cycle_count - 1
            ethernetController.reconnection(ConfigInfo)
            print("*** Restarting MPUSH *** ")
            print(ethernetController.MPushStartFromConfig(desiredShots, ConfigInfo))
        except KeyboardInterrupt: 
            print("User interrupted program by pressing Ctrl-C.")
            break


the main acquisition loop consists of repeating a single acquisition cycle until the desired number of 
acquisitions is reached. 
A connection error can always occur, so we handle this exception by trying to re-connect and restart MPUSH mode. 

*  **singleAcquistionCycle(ethernetController, dataParser, ConfigInfo)**: 
    consists of receiving, parsing and savine the data.  
    this will be explained in more details in the chapter :ref:`Single Acq`

* **ethernetController.reconnection(ConfigInfo)**: 
    attempt to reconnect. if 5 attempts fail, will raise a ``RuntimeError``

    Internally this will: 
    * send a ``KILL Socket`` command to the hardware.
    * reopen command and push sockets.
    * update installed transient recorder list.
    * reconfigure the the hardware.
    * Clear the internal ``pushBuffer``

* **ethernetController.MPushStartFromConfig(desiredShots, ConfigInfo)**: 
    Restart MPUSH see :ref:`Start Mpush`

.. _Single Acq:
9. Single acquisition cycle
-------------------------------

A single acquisition cycle consists of :
    * receiving the data from the push socket.
    * parsing the push data.  
    * saving the data to file.  

.. code-block:: python

    def singleAcquistionCycle(ethernetController, dataParser, ConfigInfo):
        
        startTime =  datetime.now()
        ethernetController.recvPushData() 
        stopTime =  datetime.now()

        (dataValid,
        dataSets,
        time_stamp,
        analogue_shots,
        pc_shots) = dataParser.parseDataFromBuffer(ConfigInfo,
                                                    ethernetController,
                                                    desiredShots)

        if (dataValid): 
            dataParser.savePushDataToFile(dataSets,
                                        ConfigInfo,
                                        startTime,stopTime,
                                        ethernetController.hardwareInfos,
                                        time_stamp,
                                        analogue_shots, 
                                        pc_shots,
                                        desiredShots,
                                        ACQUISPERFILE ) 

        else :
            if (LOGPUSHDATA): 
                controllerTimeMs = ethernetController.getMilliSecs()
                Idn = ethernetController.getID()
                print("Invalid data received with timestamp:",controllerTimeMs)
                dataParser.pushDataLog(logFilePath,
                                        ethernetController.pushBuffer,
                                        Idn,
                                        controllerTimeMs,
                                        ConfigInfo)
            # if data is not valid clear buffer until next occurrence of xff xff 
            dataParser.removeInvalidDataFromBuffer(ethernetController.pushBuffer)

* **ethernetController.recvPushData()**:
    Fills the internal ``ethernetController.pushBuffer`` with the received raw binary. 
    This function will wait until ``ethernetController.pushBuffer`` is completely filled.
    Internally ``ethernetController.BufferSize`` determines ``ethernetController.pushBuffer``size.

    This function could raise ``ConnectionError``.

* **dataParser.parseDataFromBuffer(ConfigInfo, ethernetController, desiredShots)**   
    Parse the ``ethernetController.pushBuffer`` and checks for data validity. 
    returns a list containing the requested data sets to be later stored in data files. 
    for more information see: 
    :py:meth:`Licel.licel_data.DataParser.parseDataFromBuffer`

* **dataParser.savePushDataToFile(dataSets, ConfigInfo, startTime,stopTime, ethernetController.hardwareInfos,
                                   time_stamp, analogue_shots, pc_shots, desiredShots, ACQUISPERFILE )**
    save file in the directory specified in the .ini File.
    for more information see :py:meth:`Licel.licel_data.DataParser.savePushDataToFile`

* **dataParser.removeInvalidDataFromBuffer(pushBuffer)**
    in case the ``ethernetController.pushBuffer`` contains invalid data, for example data was lost during the 
    transmission, we will simply discard the invalid data from the ``ethernetController.pushBuffer``

* **dataParser.pushDataLog(logFilePath, ethernetController.pushBuffer, Idn, controllerTimeMs, ConfigInfo)**
    log invalid Data. Used for trouble shooting.

10. disable push mode and close connection to the ethernet controller.
----------------------------------------------------------------------

.. code-block:: python

    
    ethernetController.MPushStop()
    ethernetController.shutdownConnection()
    ethernetController.shutdownPushConnection()


**ethernetController.MPushStop()** 
    set all the active transient recorder back to slave. 

**ethernetController.shutdownConnection()** 
    closes command socket 

**ethernetController.shutdownPushConnection()**
    closes push socket.



