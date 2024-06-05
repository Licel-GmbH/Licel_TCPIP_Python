**mpush source documentation** 
================================

in what follow we will describe section by section the mpush example. 

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

    ethernetController = licel_tcpip.licelTCP (ip, port)
    dataParser = licel_data.Data()
    ConfigInfo = licel_Config.Config("Acquis.ini")
    pushBuffer = bytearray()


    
* **ethernetController**: is the class responsible for handling the communication with the hardware.

* **dataParser**: class holding method for parsing ``pushBuffer``.

* **ConfigInfo**: class holding method for reading and storing configuration from the ini file
                passed as argument, in this example ``Acquis.ini``  

* **pushBuffer**: buffer to temporarily store raw data transmitted for the transient recorder.

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

5. Get IDN and detect timestamp endianess
-----------------------------------------

.. code-block:: python 

    bigEndianTimeStamp = False
    Idn = ethernetController.getID()
    if (Idn.find("ColdFireEthernet") != -1) : 
        bigEndianTimeStamp = True     

Ethernet controller returning ``ColdFireEthernet`` in their id string deliver timestamp
as big endian. 

Ethernet controller returning ``Arm`` in their id string deliver timestamp
as little endian. 

we need this information later, when parsing the push buffer to correctly extract the timestamp
for each dataset.

6. Get the total number of transient recorder in the system and their respective hardware information
---------------------------------------------------------------------------------------------------------
.. code-block:: python 

    
    Tr=ethernetController.PopulateTrList()   
    TRHardwareInfos = ethernetController.getTrHardwareInfo(Tr, ConfigInfo)

* **ethernetController.PopulateTrList()**: list all the detected transient recorder in the system. 
    if one or more transient recorder are detected, it will return a transient recorder object
    which will be used to communication with the transient recorder hardware. 

* **ethernetController.getTrHardwareInfo(Tr, ConfigInfo)**: get hardware information for each 
    active transient recorder in the configuration. Active transient recorder means that at 
    least one memory (analogue or photon counting) is set to true in the configuration file. 
    If all memories (analogue and photon counting) are set to ``False`` in the configuration
    file, the transient recorder is considered inactive and will be ignored. see :ref:`TRini-File` 

7. Configure the active transient records hardware in the system as specified in the configuration file
---------------------------------------------------------------------------------------------------------
.. code-block:: python 

    Tr.configure(ConfigInfo)

* the current supported configuration is :
    * Discriminator level  
    * pretrigger 
    * Threshold 
    * frequency divider 
    * maximum number of shots 
    * input range 

for more information about the supported configuration see :ref:`TRini-File`

8. Get the Data sets count and start the mpush acquisition
----------------------------------------------------------- 

.. code-block:: python 

    ConfigInfo.setDatasetsCount(desiredShots, TRHardwareInfos)
    print(ethernetController.MPushStartFromConfig(desiredShots, ConfigInfo, TRHardwareInfos)) 

* **ConfigInfo.setDatasetsCount(desiredShots, TRHardwareInfos)**: sets the number of expected   
    raw bytes: ``ConfigInfo.exceptedByte`` and push buffer size: ``ConfigInfo.BufferSize``
    the raw bytes to be received varies depending on the active number of datasets as well as 
    the number of bins in configuration, the hardware type (TR-12bit/16bit) and the desired number of shots.  

* **ethernetController.MPushStartFromConfig(desiredShots, ConfigInfo, TRHardwareInfos)**: 
    starts the mpush acquisition mode   

9. Acquisition loop
-------------------------

the Acquisition loop consists of :
    * receiving the data from the push socket.
    * parsing the push data.  
    * saving the data to file.  

.. code-block:: python

    cycle_count = 0
    while (cycle_count < ACQUISTION_CYCLES):
        
        startTime =  datetime.now()
        ethernetController.recvPushData(pushBuffer, ConfigInfo.BufferSize) 
        stopTime =  datetime.now()

        (dataValid,
         dataToWrite,
         time_stamp,
         analogue_shots,
         pc_shots) = dataParser.parseDataFromBuffer(pushBuffer,
                                                    ConfigInfo,
                                                    bigEndianTimeStamp,
                                                    desiredShots, 
                                                    TRHardwareInfos)
        if (dataValid): 
            cycle_count += 1
            dataParser.saveFile(dataToWrite,
                                ConfigInfo,
                                startTime,stopTime,
                                TRHardwareInfos,
                                time_stamp,
                                analogue_shots, 
                                pc_shots,
                                desiredShots,
                                ACQUISPERFILE ) 
        else :
            if (LOGPUSHDATA): 
                controllerTimeMs = ethernetController.getMilliSecs()
                print("Invalid data received with timestamp:",controllerTimeMs)
                dataParser.pushDataLog(logFilePath,
                                       pushBuffer,
                                       Idn,
                                       controllerTimeMs,
                                       ConfigInfo)
            # if data is not valid clear buffer until next occurrence of xff xff 
            dataParser.removeInvalidDataFromBuffer(pushBuffer)

* **ethernetController.recvPushData(pushBuffer, ConfigInfo.BufferSize)**: 
    Fills the ``pushBuffer`` with raw binary received from the ethernet controller. 
    this function will block until ``pushBuffer`` is completely filled. 
    ``ConfigInfo.BufferSize`` determines ``pushBuffer`` size to be filled.

* **dataParser.parseDataFromBuffer(pushBuffer, ConfigInfo, bigEndianTimeStamp, desiredShots, TRHardwareInfos)**   
    Parse the ``pushBuffer`` and checks for data validity. 
    returns a list containing the requested data sets to be later stored in data files. 
    A data set is    
    for more information see: 
    :py:meth:`Licel.licel_data.DataParser.parseDataFromBuffer`

* **dataParser.saveFile(dataTowrite, ConfigInfo, startTime,stopTime,TRHardwareInfos,time_stamp, analogue_shot_dict,pc_shot_dict, desiredShots, ACQUISPERFILE )**                     
    save file in the directory specified in the .ini File. 
    for more information see :py:meth:`Licel.licel_data.DataParser.saveFile`

* **dataParser.removeInvalidDataFromBuffer(pushBuffer)**
    in case the ``pushBuffer`` contains invalid data, for example data was lost during the 
    transmission, we will simply discard the invalid data from the ``pushBuffer``

10. disable push mode and close connection to the ethernet controller.
----------------------------------------------------------------------

.. code-block:: python

    
    ethernetController.MPushStop(Tr, ConfigInfo)
    ethernetController.shutdownConnection()
    ethernetController.shutdownPushConnection()


**ethernetController.MPushStop(Tr, ConfigInfo)** 
    set all the active transient recorder back to slave. 

**ethernetController.shutdownConnection()** 
    closes command socket 

**ethernetController.shutdownPushConnection()**
    closes push socket.



