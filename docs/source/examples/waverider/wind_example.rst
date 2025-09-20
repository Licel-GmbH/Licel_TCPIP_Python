waverider example
===================

The Licel Waverider module is designed to be used in pulsed coherent Doppler Wind systems.
It takes the output of balanced fiber detector together with a synchronizing trigger pulse and computes
power spectra from an 250MHz AC coupled 14bit ADC signal which are then averaged and transmit-
ted over Ethernet to a PC. 

The waverider python API currently supports **waverider with a single trigger input**.

the waverider_example.py demonstrates how to use the Python TCP/IP API to: 
    * Configure the waverider paramters (fft size, shots, etc..)
    * Acquire the Power spectra data
    * save the power spectra data to a netcdf file

the detailed waverider manual is to be found under: 
https://licel.com/wind.htm


Call the script using:

.. code-block:: RST

        python3 waverider_example.py --ip <ip> --port <port>  --acq <num acquis> --shots <num shots>
                         --acquis_per_file <acquis per file> --log 

        Argument List : 
        -h, --help           show this help message and exit
        --ip IP              waverider ip address
        --port PORT          waverider command port
        --shots SHOTS        number of shots per acquisition
        --fft_size FFT_SIZE  number of adc samples that goes into computing one fft. Accepted values: 32,64,128,256,512,1024.
        --range RANGE        Defines the maximum distance the ADC trace should cover in meters. Max range is 39320 meters 

.. toctree::
    :maxdepth: 1

    waverider_example_src

