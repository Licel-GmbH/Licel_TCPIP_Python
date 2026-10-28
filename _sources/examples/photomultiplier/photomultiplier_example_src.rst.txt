Photomultiplier example source documentation
===============================================


1. import modules
------------------

.. code-block:: python

	from Licel import licel_tcpip, photomultiplier
	import argparse


* **licel_tcpip**: module required for communication with the ethernet controller.
* **photomultiplier**: module providing the `photomultiplier` wrapper class.
* **argparse**: for parsing command line arguments in the example.


2. Command-line interface
-------------------------

The example uses a CLI helper to parse the following options:

.. code-block:: python

	argparser.add_argument('--ip', type=str, default = "10.49.234.234")
	argparser.add_argument('--port', type=int, default=2055)
	argparser.add_argument('--PMT', type=int, default=0)
	argparser.add_argument('--voltage', type=int, default=0)


3. Initialize and open connection
---------------------------------

Create the `EthernetController` and the `photomultiplier` instance and open the command socket:

.. code-block:: python

	ethernetController = licel_tcpip.EthernetController(ip, port)
	pmt = photomultiplier.photomultiplier(ethernetController)

	ethernetController.openConnection()

* **ethernetController.openConnection()** — opens the command socket to the controller.


4. Query device and list installed PMTs
---------------------------------------

Get controller identity and capabilities and list installed PMTs:

.. code-block:: python

	print(ethernetController.getID())
	print(ethernetController.getCapabilities())
	print(pmt.listInstalledPMT())

* **ethernetController.getID()** — returns the controller identification string.
* **ethernetController.getCapabilities()** — returns a capability string (e.g. contains `PMT` when PMT support is available).
* **pmt.listInstalledPMT()** — checks which PMTs are physically installed and returns a dict mapping PMT number to status.


5. Set and read PMT high voltage
--------------------------------

Set a PMT high-voltage and read it back:

.. code-block:: python

	print(pmt.setHV(pmt_device_number, voltage))
	print(pmt.getHV(pmt_device_number))

* **pmt.setHV(device, voltage)** — sets the HV for the specified PMT device and returns the controller response.
* **pmt.getHV(device)** — queries the current HV value for the specified PMT.


6. Restore and close
---------------------

After the example finishes, reset the PMT voltage to 0V and shut down the command socket:

.. code-block:: python

	print(pmt.setHV(pmt_device_number, 0))
	ethernetController.shutdownConnection()

* **ethernetController.shutdownConnection()** — closes the command socket.




