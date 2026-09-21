SilentState Runtime Example
=================================================

The ``SilentStat_Runtime_example.py`` script changes the SilentState delay
configuration **at runtime** and can activate or deactivate the feature. The
pre-trigger and post-trigger block delay times are applied directly to the
controller **without** saving them to flash memory. The default state (on or
off) after a controller reboot remains unchanged.

Call the script using:

.. code-block:: RST

        python3 SilentStat_Runtime_example.py --ip <ip> --port <port> --on|--off
                                              [--preTrigDelay <us> --postTrigDelay <us>]

        Argument List :
        --ip               ip address of the controller you wish to communicate with.
        --port             command socket port number, (default 2055)
        --on / --off       activate or deactivate the SilentState feature (required, mutually exclusive)
        --preTrigDelay     pre-trigger block delay in microseconds (optional)
        --postTrigDelay    post-trigger block delay in microseconds (optional)

        Note: --preTrigDelay and --postTrigDelay must be supplied together.

In what follows, we describe the example section by section.

1. Import modules
-----------------

.. code-block:: python

    import argparse
    from Licel import licel_tcpip

* **argparse**: module for parsing command-line arguments.
* **Licel.licel_tcpip**: module required for communication with the Ethernet
  controller. The ``EthernetController`` instance exposes the SilentState API
  through its ``SilentStat`` attribute.

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
        parser.add_argument("--preTrigDelay",  type=int, metavar="US",  help="Pre-trigger block delay in microseconds (optional)")
        parser.add_argument("--postTrigDelay", type=int, metavar="US",  help="Post-trigger block delay in microseconds (optional)")

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--on",  action="store_true", help="Activate the silent stat")
        group.add_argument("--off", action="store_true", help="Deactivate the silent stat")

        args = parser.parse_args()

        if (args.preTrigDelay is None) != (args.postTrigDelay is None):
            parser.error("--preTrigDelay and --postTrigDelay must both be specified together")

        return args

* **commandLineInterface()**: parses and returns the command-line arguments.
    * **--ip** / **--port**: connection parameters of the controller.
    * **--preTrigDelay** / **--postTrigDelay**: optional block delay times in
      microseconds (see the timing diagram in the SilentState overview).
    * **--on** / **--off**: a *mutually exclusive* and *required* group that
      activates or deactivates the feature.
* The final check enforces that the two delays are either **both** provided or
  **both** omitted — supplying only one is rejected with an error.

4. Main entry point and connection
-----------------------------------

.. code-block:: python

    def main():
        myArguments = commandLineInterface()
        ip   = myArguments.ip
        port = myArguments.port
        preTriggerDelay = myArguments.preTrigDelay
        postTriggerDelay = myArguments.postTrigDelay

        ethernetController = licel_tcpip.EthernetController(ip, port)
        ethernetController.openConnection()

* Extracts the parsed arguments.
* **ethernetController**: creates an Ethernet controller instance bound to the
  given IP address and command port.
* **ethernetController.openConnection()**: establishes the TCP connection on the
  command port.

5. Apply the block delays (optional)
------------------------------------

.. code-block:: python

        if preTriggerDelay is not None and postTriggerDelay is not None:
            print(ethernetController.SilentStat.setDelay(int(preTriggerDelay), int(postTriggerDelay)))
            preTrig, postTrig = ethernetController.SilentStat.getDelay()
            print("Pre-trigger delay  :", preTrig,  "us")
            print("Post-trigger delay :", postTrig, "us")

* **SilentStat.setDelay(pre, post)**: sends the new pre-/post-trigger block delay
  times (in microseconds) to the controller. These values define the silence
  window applied around each trigger.
* **SilentStat.getDelay()**: reads the delays back from the controller to confirm
  they were applied, returning them as a ``(preTrigger, postTrigger)`` tuple.
* This block runs only when both delays were supplied on the command line.

6. Activate or deactivate the feature
-------------------------------------

.. code-block:: python

        if myArguments.on:
            print(ethernetController.SilentStat.ON())
        elif myArguments.off:
            print(ethernetController.SilentStat.OFF())

        print("State :", ethernetController.SilentStat.getState())

        ethernetController.shutdownConnection()

* **SilentStat.ON()**: activates the feature. The controller will now delay the
  ``STAT?`` command sent to the selected transient recorder during the configured
  silence window around every trigger. All other commands are still forwarded
  instantaneously.
* **SilentStat.OFF()**: deactivates the feature; the ``STAT?`` command is no
  longer delayed.
* **SilentStat.getState()**: queries and prints the resulting state for
  confirmation.
* **ethernetController.shutdownConnection()**: cleanly closes the TCP connection.

.. note::

   Changes made here are **volatile**. To make the configuration survive a
   reboot, persist it to flash with ``SilentStat_Store_example.py``.

7. Script entry point
---------------------

.. code-block:: python

    if __name__ == "__main__":
        main()

* Ensures that ``main()`` is only called when the script is executed directly
  (not when imported as a module).
