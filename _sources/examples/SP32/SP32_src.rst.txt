SP32 Example Source Documentation
=====================================

In what follows, we will describe section by section the SP32 example.

1. Import modules
-----------------

.. code-block:: python

    from Licel import licel_tcpip, licel_SP32, licel_SP32_Config
    import time
    from datetime import datetime
    import argparse

* **Licel**:
    * **licel_tcpip**: module required for communication with the Ethernet controller.
    * **licel_SP32**: module providing the high-level API for the SP32 digitizer.
    * **licel_SP32_Config**: module for parsing and handling SP32 configuration files.

* **time**: module for adding delays (e.g., ``time.sleep()``).
* **datetime**: module for acquiring and storing timestamps.
* **argparse**: module for parsing command-line arguments.

2. Define acquisition constants
-------------------------------

.. code-block:: python

    CURRENTLIMIT = 0.400 #in mA

* **CURRENTLIMIT**: safety threshold (in mA) for the PMT anode current. 
  If this current limit is exceeded, the PMT detector might be damaged. 


3. Command-line interface function
----------------------------------

.. code-block:: python

    def commandLineInterface():
        argparser = argparse.ArgumentParser(description='SP32 example ')
        argparser.add_argument('--ip', type=str, default = "10.49.234.234",
                                help='ethernet controller ip address')
        argparser.add_argument('--port', type=int, default=2055,
                                help='ethernet controller command port')
        argparser.add_argument('--shots', type=int, default=100,
                                help='number of shots to acquire per run')
        argparser.add_argument('--acq', type=int, default=100,
                                help='number of acquisition to perform')
        args = argparser.parse_args()
        return args

* **commandLineInterface()**: parses and returns command-line arguments.
    * **--ip**: IP address of the Ethernet controller (default: ``10.49.234.234``).
    * **--port**: command port of the controller (default: ``2055``).
    * **--shots**: number of shots per acquisition cycle (default: ``100``).
    * **--acq**: total number of acquisition cycles to perform (default: ``100``).

4. Single acquisition and save cycle
------------------------------------

.. code-block:: python

    def AcquireAndSave(sp32: licel_SP32.SP32, Config: licel_SP32_Config.SP32_Config,
                       Shots_To_Acquire: int):
        
        starttime = datetime.now()
        print(sp32.startAcquisition(Shots_To_Acquire))

        state,  shots, targetshots, current, timestamp = sp32.getStatus()
        while state != 'Idle':
            state,  shots, targetshots, current, timestamp = sp32.getStatus()
            time.sleep(0.1)
            if current > CURRENTLIMIT:
                print(f"Current limit exceeded: {current} mA. Setting HV to 0")
                sp32.setHV(0)
                sp32.stopAcquisition()
                raise Exception(f"Current limit exceeded: {current} mA. Setting HV to 0") 

        shots,data = sp32.getData()
        stoptime = datetime.now()
        sp32.saveSP32Data(Config, starttime, stoptime,"EH",shots, data)
        return shots,data

* **AcquireAndSave()**: encapsulates a complete acquisition and save cycle.
    * Records the start time with ``datetime.now()``.
    * Calls ``sp32.startAcquisition(Shots_To_Acquire)`` to begin data collection.
    * Polls the device status repeatedly until acquisition completes (state becomes ``'Idle'``).
    * On each poll iteration, checks if the on-board current sensor exceeds ``CURRENTLIMIT``.
      If exceeded, sets HV to zero, stops acquisition and raises an exception.
    * Once acquisition is complete, calls ``sp32.getData()`` to retrieve the acquired traces.
    * Records the stop time.
    * Saves the acquired data using ``sp32.saveSP32Data()`` with the file prefix ``"EH"``
      and the acquisition time range.
    * Returns the number of shots acquired and the data array.

5. Main entry point and initialization
--------------------------------------

.. code-block:: python

    def main():
        myArguments = commandLineInterface()    
        ip = myArguments.ip
        port = myArguments.port
        Shots_To_Acquire = myArguments.shots
        RUNS = myArguments.runs

        ethernetController = licel_tcpip.EthernetController (ip, port)
        sp32 = licel_SP32.SP32(ethernetController)
        Config = licel_SP32_Config.SP32_Config("SP32.ini")
        Config.readConfig()
        ethernetController.openConnection()

* **commandLineInterface()**: parses and extracts command-line arguments.
* **ethernetController**: creates an Ethernet controller instance bound to the specified
  IP address and command port.
* **sp32**: creates an SP32 digitizer instance, bound to the Ethernet controller.
* **Config**: creates a configuration object and reads settings from ``SP32.ini``.
* **ethernetController.openConnection()**: establishes the TCP connection on the command
  port (used for control commands).

6. Query and display hardware information
-----------------------------------------

.. code-block:: python

    print("*** GET SP32 hardware informations ****")
    print(ethernetController.getID())
    print(sp32.getHardwareID())
    print(sp32.getCapabilites())
    print(sp32.getCurrent())
    print(sp32.getDieTemperature())
    print(sp32.getPCBTemperature())
    print(ethernetController.getMilliSecs())

* **ethernetController.getID()**: retrieve and display the controller ID.
* **sp32.getHardwareID()**: retrieve and display hardware revision, bin length, max range bins,
  bin size, max shots, and other hardware details.
* **sp32.getCapabilites()**: retrieve and display the controller capabilities (e.g., channel count).
* **sp32.getCurrent()**: retrieve and display the current ADC value of the on-board high-voltage
  supply current sensor.
* **sp32.getDieTemperature()**: retrieve and display the die temperature in degrees Celsius.
* **sp32.getPCBTemperature()**: retrieve and display the PCB board temperature.
* **ethernetController.getMilliSecs()**: retrieve and display the millisecond counter of the controller.

7. Configure SP32 parameters
----------------------------

.. code-block:: python

    print("*** CONFIGURE SP32 PARAMETERS ****")
    print(sp32.setDiscriminator(Config.SP32param.discriminator))
    print(sp32.setHV(Config.SP32param.HV))
    time.sleep(0.1)
    print(sp32.getHV())
    print(sp32.setTimeResoultion(Config.SP32param.binwidth_ns))
    print(sp32.setRange(Config.SP32param.noBins))
    print(sp32.closeShutter())
    print(sp32.getShutterPosition())
    print(sp32.openShutter())
    print(sp32.getShutterPosition())

* **sp32.setDiscriminator()**: sets the discriminator level read from the configuration file.
* **sp32.setHV()**: sets the high voltage for the PMT(s) from the configuration.
* **time.sleep(0.1)**: brief delay to allow HV to stabilize.
* **sp32.getHV()**: verify and display the currently set HV value.
* **sp32.setTimeResoultion()**: sets the digitizer time resolution (in nanoseconds) from the config.
  Internally, the device may activate wide-memory mode if needed.
* **sp32.setRange()**: sets the number of range bins to acquire.
* **sp32.closeShutter()**: closes the spectrometer shutter (if equipped).
* **sp32.getShutterPosition()**: queries and displays the current shutter position.
* **sp32.openShutter()**: opens the spectrometer shutter.
* **sp32.getShutterPosition()** (again): verify the shutter is open.

8. Main acquisition loop
------------------------

.. code-block:: python

    print("****************** Starting Acquisition ***********************")
    print(sp32.stopAcquisition())
    cycle = 0
    while cycle < RUNS: 
        AcquireAndSave(sp32, Config, Shots_To_Acquire)
        cycle += 1  
    print("******************Acquisition Finished, Shutting down...*************")
    print(sp32.setHV(0))
    ethernetController.shutdownConnection()

* **sp32.stopAcquisition()**: ensures no acquisition is currently running before starting
  the main loop.
* **Main loop**: iterates ``RUNS`` times, calling ``AcquireAndSave()`` in each cycle.
  Each cycle acquires the configured number of shots and saves the data.
* **sp32.setHV(0)**: sets the HV to zero at the end to safely shut down the detector.
* **ethernetController.shutdownConnection()**: closes the TCP connection to the Ethernet
  controller, cleanly shutting down the session.

9. Script entry point
---------------------

.. code-block:: python

    if __name__ == "__main__":
        main()

* Ensures that ``main()`` is only called when the script is executed directly (not when imported
  as a module).
