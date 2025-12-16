Powermeter example source documentation
==========================================


1. import modules
------------------

.. code-block:: python

	from Licel import licel_tcpip, powermeter
	import argparse


* **licel_tcpip**: module required for communication with the ethernet controller.
* **powermeter**: module providing the `powermeter` wrapper around powermeter-specific commands.
* **argparse**: for parsing command line arguments in the example.


2. Command-line interface
-------------------------

The example uses a CLI helper to parse the following options:

.. code-block:: python

	argparser.add_argument('--ip', type=str, default = "10.49.234.234")
	argparser.add_argument('--port', type=int, default=2055)
	argparser.add_argument('--acq', type=int, default=100)
	argparser.add_argument('--channel', type=int,  default=0)
	argparser.add_argument('--internalTrigger', action=argparse.BooleanOptionalAction)


3. Initialize objects and open connections
------------------------------------------

Create the `EthernetController` and the `powermeter` instance and open both the command
and push sockets:

.. code-block:: python

	ethernetController = licel_tcpip.EthernetController(ip, port)
	Powermeter = powermeter.powermeter(ethernetController)

	ethernetController.openConnection()
	ethernetController.openPushConnection()

* **ethernetController.openConnection()** — opens the command socket to the controller.
* **ethernetController.openPushConnection()** — opens the push socket used for streaming data.


4. Verify device capability and select channel
----------------------------------------------

Check that the controller supports the powermeter subcomponent and select the ADC channel:

.. code-block:: python

	print(ethernetController.getID())
	capability = ethernetController.getCapabilities()
	if capability.find('POW') == -1:
		raise RuntimeError("Missing capabilities POW")

	print(Powermeter.selectChannel(channel))

* **ethernetController.getCapabilities()** — returns a capability string that should contain "POW" if powermeter is supported.
* **Powermeter.selectChannel(channel)** — selects the ADC input used for subsequent acquisitions (0 = photodiode, 2 = powermeter).


5. Optional: enable internal trigger
------------------------------------

The example can enable the controller internal trigger simulation. Use when `--internalTrigger` is set:

.. code-block:: python

	if SimTrig:
		print(Powermeter.startInternalTrigger())

* **Powermeter.startInternalTrigger()** — activates the internal trigger simulation.


6. Start acquisition loop (push mode)
----------------------------------------

Start push-mode acquisition and read lines from the push socket.
In this mode the Powermeter will automatically send data on the push socket once started. 
The example reads `ACQUISTION_CYCLES` lines, each containing timestamp, pulse amplitude and trigger number:

.. code-block:: python

	print(Powermeter.Start())
	for i in range(0, ACQUISTION_CYCLES):
		timestamp, pulseAmplitude, trigger_num = Powermeter.getPowermeterPushData()
		print(f"Pulse amplitude = {pulseAmplitude}, controller timestamp {timestamp} ms, trigger number {trigger_num}")
  	print(Powermeter.Stop())


* **Powermeter.Start()** — starts powermeter push acquisition on the controller.
* **Powermeter.getPowermeterPushData()** — returns a tuple `(timestamp, pulseAmplitude, trigger_num)` read from the push socket.
    * **timestamp** : EthernetController time since start in milliseconds. 
    * **pulseAmplitude** : The calculated pulse amplitude of the acquired trace. The number represents the ADC raw value. 
    * **trigger_num** : represents the trigger that caused the data to be collected.

* **Powermeter.Stop()** — stops the powermeter push acquisition.


7. Acquire single-trace 
-----------------------------------------

Request a single trace over the command socket:

.. code-block:: python

	singleTraceData = Powermeter.getTrace()
	print(singleTraceData)

* **Powermeter.getTrace()** — requests a single trace over the command socket and returns a list of integer samples.


8. Disable internal trigger and close sockets
------------------------------------------------

If an internal trigger was activated, stop it. Then shut down push and command sockets:

.. code-block:: python

	if SimTrig:
		print(Powermeter.stopInternalTrigger())

	ethernetController.shutdownPushConnection()
	ethernetController.shutdownConnection()

* **Powermeter.stopInternalTrigger()** — stop internal trigger simulation.
* **ethernetcontroller.shutdownPushConnection()** and **shutdownConnection()** — close push and command sockets respectively.



