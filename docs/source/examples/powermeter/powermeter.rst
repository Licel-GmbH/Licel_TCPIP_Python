Powermeter example
====================== 

The ``powermeter_example.py`` demonstrate the use powermeter device.

Call the script using:

.. code-block:: RST

        python3 powermeter_example.py --ip <ip> --port <port>  --acq <num acquis> --channel <channel>

        Argument List : 
        --ip        ip address of the ethernetController we wish to communicate with. 
        --port      command socket port number, (default 2055)
        --acq       desired number of acquisitions
        --channel   Selects the ADC channel for the data acquisition. 
                    channel can either be 0 for photodiode or 2 for powermeter. (default 0)       

The powermeter can be operate in 2 modes : 

1. **trace mode**: acquire a single pulse and returns the the pulse trace

2. **push mode**: For every received trigger, the powermeter will calculate the pulse amplitude
                  and automatically send it without further request from the host computer. 