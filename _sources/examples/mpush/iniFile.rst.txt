
**Acquis.ini File**
====================

The initialization file acquis.ini contains definition sections for each transient recorder.
The data here corresponds to the values set while configuring the transient recorders.
The data entries may appear in a different order within a section named [TR<address>].
Here, the section for the transient recorder with the device address 0 is shown

.. _TRini-File: 

Transient recorder configuration 
--------------------------------

.. code-block:: RST

    [TR0]
    Range = 1
    Pretrigger = 0
    FreqDivider = 2
    ShotLimit = 1000
    Threshold = 0 
    Discriminator = 0

    AnalogA = TRUE
    Analog B = False
    Analog C = False
    AnalogD = False

    PC A = TRUE
    PC B = False
    PC C = False
    PC D = False

    PolarisationA = 1
    polarisationB = 2
    PolarisationC = 3
    PolarisationD = 4

    PolarisationApc = 1
    PolarisationBpc = 2
    PolarisationCpc = 3
    PolarisationDpc = 4

    A-binsA = 16000
    A-BinsB = 16000
    A-binsC = 16000
    A-binsD = 16000

    P-binsA = 16000
    P-binsB = 14800
    P-binsC = 1000
    P-binsD = 16000

    WavelengthA = 534,000000
    WavelengthB = 512,000000
    WavelengthC = 513,000000
    WavelengthD = 514,000000

    WavelengthApc = 600,000000
    WavelengthBpc = 610,000000
    WavelengthCpc = 620,000000
    WavelengthDpc = 630,000000

    LaserA = 1
    LaserB = 2
    LaserC = 3
    LaserD = 4

    PM = 850,000000
    PM2 = 3,000000
    PM3 = 5,000000
    PM4 = 7,000000

    PM1pc = 850,000000
    PM2pc = 4,000000
    PM3pc = 6,000000
    PM4pc = 8,000000

A section always begins with [TR<n>] where n indicates the address of the transient recorder.

* **Range** : input range of the transient recorder. Valid values are
        * 0  : 0 .. 500 mV
        * 1  : 0 .. 100 mV
        * 2  : 0 ..  20 mV

* **FreqDivider** : Set the frequency divider, it changes the sampling rate before 
                    the summation, so with FreqDivider value of 0 and bin width 3.75m you will get 3.75m range resolution.
                    With a FreqDivider of 8 you will get 30m range resolution.
                    Valid values are 0, 1, 2 ,4, 8, 16, 32, 64, 128.

* **ShotLimit**   : Sets the maximum number of shots that the TR should acquire.
                    valid values are arbitrary number between 2 and 64K

* **Discriminator** : level between 0 and 63

* **Pretrigger**: The pretrigger is 1/16 of the hardware tracelength.
                  The command can be used only if the ``TRHardwareInfo['HWCAP']`` contains the bits 0xF9

                  * 0 : disable pretrigger
                  * 1 : enable pretrigger 

                  For more info see https://licel.com/manuals/TR40-16bit3U_Manual.pdf#subsection.3.8

* **Threshold** : Sets the damping state to either on or off
    * 0 : damping state off 
    * 1 : damping state on 

|

* **AnalogA** : (TRUE | FALSE) Enable or disable analog acquisition for memory A
* **Analog B** : (TRUE | FALSE) Enable or disable analog acquisition for memory B
* **Analog C** : (TRUE | FALSE) Enable or disable analog acquisition for memory C
* **AnalogD** : (TRUE | FALSE) Enable or disable analog acquisition for memory D

|

* **A-binsA** : number of analogue bins to be read out from mem A. :ref:`max number of bins <polarisationvalidvalue>`
* **A-BinsB** : number of analogue bins to be read out from mem B. :ref:`max number of bins <polarisationvalidvalue>`
* **A-binsC** : number of analogue bins to be read out from mem C. :ref:`max number of bins <polarisationvalidvalue>`
* **A-binsD** : number of analogue bins to be read out from mem D. :ref:`max number of bins <polarisationvalidvalue>`

|

* **P-binsA**: number of photon counting bins to be read out from mem A. :ref:`max number of bins <polarisationvalidvalue>`
* **P-binsB**: number of photon counting bins to be read out from mem B. :ref:`max number of bins <polarisationvalidvalue>`
* **P-binsC**: number of photon counting bins to be read out from mem C. :ref:`max number of bins <polarisationvalidvalue>`
* **P-binsD**: number of photon counting bins to be read out from mem D. :ref:`max number of bins <polarisationvalidvalue>`

|

* **PC A** : (TRUE | FALSE) Enable or disable photon counting acquisition for memory A
* **PC B** : (TRUE | FALSE) Enable or disable photon counting acquisition for memory B
* **PC C** : (TRUE | FALSE) Enable or disable photon counting acquisition for memory C
* **PC D** : (TRUE | FALSE) Enable or disable photon counting acquisition for memory D

|

* **PolarisationA** : detection polarization for analogue mem A. see :ref:`Polarisation value <polarisationvalidvalue>`
* **PolarisationB** : detection polarization for analogue mem B. see :ref:`Polarisation value <polarisationvalidvalue>`
* **PolarisationC** : detection polarization for analogue mem C. see :ref:`Polarisation value <polarisationvalidvalue>`
* **PolarisationD** : detection polarization for analogue mem D. see :ref:`Polarisation value <polarisationvalidvalue>`

|

* **PolarisationApc** : detection polarization for photon counting mem A. see :ref:`Polarisation value <polarisationvalidvalue>`
* **PolarisationBpc** : detection polarization for photon counting mem B. see :ref:`Polarisation value <polarisationvalidvalue>` 
* **PolarisationCpc** : detection polarization for photon counting mem C. see :ref:`Polarisation value <polarisationvalidvalue>` 
* **PolarisationDpc** : detection polarization for photon counting mem D. see :ref:`Polarisation value <polarisationvalidvalue>`

|

* **PM** : Photomultiplier voltage for analogue memory A
* **PM2**: Photomultiplier voltage for analogue memory B
* **PM3**: Photomultiplier voltage for analogue memory C
* **PM4**: Photomultiplier voltage for analogue memory D

|

* **PM1pc**: Photomultiplier voltage for photon counting memory A
* **PM2pc**: Photomultiplier voltage for photon counting memory B
* **PM3pc**: Photomultiplier voltage for photon counting memory C
* **PM4pc**: Photomultiplier voltage for photon counting memory D

|

* **WavelengthA**: laser wavelength assigned to analogue memory A 
* **WavelengthB**: laser wavelength assigned to analogue memory B 
* **WavelengthC**: laser wavelength assigned to analogue memory C 
* **WavelengthD**: laser wavelength assigned to analogue memory D 

|

* **WavelengthApc**: laser wavelength assigned to photon counting memory A 
* **WavelengthBpc**: laser wavelength assigned to photon counting memory B 
* **WavelengthCpc**: laser wavelength assigned to photon counting memory C 
* **WavelengthDpc**: laser wavelength assigned to photon counting memory D 

.. _polarisationvalidvalue:

+---------------------------+---------------------+
| Polarisation value        | max number of  bins |
+===========================+=====================+
| 0 : none                  |  16300 bins         |
+---------------------------+                     |
| 1 : parallel              |                     |
+---------------------------+                     |
| 2 : crossed               |                     |
+---------------------------+                     |
| 3 : right circular        |                     |
+---------------------------+                     |
| 4 : left circular         |                     |
+---------------------------+---------------------+

Global informations 
---------------------
.. code-block:: RST

    [global_info] 
    Location = "Berlin"
    Longitude = 13,384714
    Latitude =  52,542598
    Height_asl = 45,000000
    working_directory = "C:\temp\"
    first_letter = "LI"
    Zenith = 0,000000
    Azimuth = 15,000000
    frequency1 = 120,000000
    frequency2 = 100,000000
    frequency3 = 10,000000
    frequency4 = 10,000000
    SaveOverflow = TRUE

