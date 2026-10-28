SilentState Store Example
===============================================

The ``SilentStat_Store_example.py`` script permanently saves the current
SilentState configuration (on/off state and pre-/post-trigger block delay times)
to the controller's **flash memory**. After a reboot the controller restores
these stored settings as the new default. A password is required to authorize
the store operation.

Call the script using:

.. code-block:: RST

        python3 SilentStat_Store_example.py --ip <ip> --port <port> --password <password>

        Argument List :
        --ip               ip address of the controller you wish to communicate with.
        --port             command socket port number, (default 2055)
        --password         password authorizing the store operation (default password is 'Administrator')

In what follows, we describe the example section by section.

1. Import modules
-----------------

.. code-block:: python

    import argparse
    from Licel import licel_tcpip

* **argparse**: module for parsing command-line arguments.
* **Licel.licel_tcpip**: module required for communication with the Ethernet
  controller. The SilentState API is reached through the controller's
  ``SilentStat`` attribute.

2. Default connection constants
-------------------------------

.. code-block:: python

    DEFAULT_IP   = "10.49.234.234"
    DEFAULT_PORT = 2055

* **DEFAULT_IP**: default controller IP address used when ``--ip`` is omitted.
* **DEFAULT_PORT**: default command socket port used when ``--port`` is omitted.

3. Command-line interface function
----------------------------------

.. code-block:: python

    def commandLineInterface():
        parser = argparse.ArgumentParser(description="Control the SilentStat feature of a Licel Ethernet Controller.")
        parser.add_argument("--ip",   type=str, default=DEFAULT_IP,   help="Controller IP address (default: %(default)s)")
        parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Controller port (default: %(default)s)")
        parser.add_argument("--password", type=str, required=True, help="Password for storing configuration, Default password is 'Administrator'")

        args = parser.parse_args()

        return args

* **commandLineInterface()**: parses and returns the command-line arguments.
    * **--ip** / **--port**: connection parameters of the controller.
    * **--password**: *required* password that authorizes writing to flash. The
      default controller password is ``Administrator``.

4. Main entry point and connection
-----------------------------------

.. code-block:: python

    def main():
        myArguments = commandLineInterface()
        ip   = myArguments.ip
        port = myArguments.port
        password = myArguments.password

        ethernetController = licel_tcpip.EthernetController(ip, port)
        ethernetController.openConnection()

* Extracts the parsed arguments.
* **ethernetController**: creates an Ethernet controller instance bound to the
  given IP address and command port.
* **ethernetController.openConnection()**: establishes the TCP connection on the
  command port.

5. Display the current configuration
------------------------------------

.. code-block:: python

        print("Current SilentStat configuration:")
        preTrig, postTrig = ethernetController.SilentStat.getDelay()
        print("  State :", ethernetController.SilentStat.getState())
        print("  Pre-trigger delay  :", preTrig,  "us \r\n")
        print("  Post-trigger delay :", postTrig, "us \r\n")

* **SilentStat.getDelay()**: reads the current pre-/post-trigger block delay
  times (in microseconds), returned as a ``(preTrigger, postTrigger)`` tuple.
* **SilentStat.getState()**: reads the current on/off state.
* The current configuration is printed so the operator can confirm what is about
  to be written to flash.

6. Store the configuration to flash
-----------------------------------

.. code-block:: python

        print("Storing configuration to flash memory... \r\n")
        print(ethernetController.SilentStat.store(password))

        ethernetController.shutdownConnection()

* **SilentStat.store(password)**: writes the current SilentState settings (state
  and delays) into the controller's non-volatile flash memory. The supplied
  password authorizes the operation. After the next reboot the controller will
  restore these settings as its default.
* **ethernetController.shutdownConnection()**: cleanly closes the TCP connection.

.. note::

   Unlike ``SilentStat_Runtime_example.py`` (whose changes are volatile), the
   settings stored here **persist across power cycles**.

7. Script entry point
---------------------

.. code-block:: python

    if __name__ == "__main__":
        main()

* Ensures that ``main()`` is only called when the script is executed directly
  (not when imported as a module).
