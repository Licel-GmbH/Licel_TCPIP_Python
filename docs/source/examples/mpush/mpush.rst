Mpush example
==============

The mpush mode is the most efficient way to acquire data from multiple transient recorder. 
In this mode the ethernet controller will automatically send data to the computer as soon as 
the data is ready without further request from the computer. 

the ``mpush.py`` demonstrate the use of the mpush mode to continuously acquire data.  

Call the script using:

.. code-block:: RST

        python3 mpush.py --ip <ip> --port <port>  --acq <num acquis> --shots <num shots>
                         --acquis_per_file <acquis per file> --log 

        Argument List : 
        --ip               ip address of the ethernetController we wish to communicate with. 
        --port             command socket port number, (default 2055)
        --acq              desired number of acquisitions
        --shots            desired number of shots per acquisition
        --acquis_per_file  maximal number of acquisitions to save in a single file.
        --log, --no-log    (optional) enable logging push data when error occurs. 
                             default, when no argument is passed, the logging is disabled.   

The mpush example will read the Configuration from acquis.ini and 
Configure the transient recorders. It will then acquire the dataset(s) using the Mpush 
and save the data to a file.   

in what follow we will go through the possible ini file parameters, 
and explain each section in mpush source code. 


.. toctree::
    :maxdepth: 1

    iniFile
    mpush_src
        
