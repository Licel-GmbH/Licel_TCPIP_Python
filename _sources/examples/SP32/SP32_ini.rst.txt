SP32 INI configuration
===========================

This document describes the main settings of the ``SP32.ini`` configuration
file used by :class:`Licel.licel_SP32_Config.SP32_Config`. The file contains
global measurement metadata and device-specific parameters for the SP32
digitizer.

Example: ``SP32.ini``
------------------------

.. code-block:: ini

		[global_info]
		Location = "Berlin"
		Longitude = 13,384714
		Latitude = 52,542598
		Height_asl = 45,000000
		working_directory = "D:\\Licel_TCPIP_Python\\data"
		first_letter = "EH"
		Zenith = 0,000000
		Azimuth = 15,000000
		frequency1 = 120,000000
		frequency2 = 100,000000
		frequency3 = 10,000000
		Info = ""
		NoSafeIncompleteFiles = FALSE
		SaveOverflow = TRUE
		SyncViewer = FALSE


		[SP32]

		Discriminator = 7
		NoBins  = 1600
		Binwidth_ns  = 0,625
		HV = 850
		centralWavelength = 532.00
		nm_PerChannel = 6.2

Section: ``global_info``
----------------------------

- **Location**: Measurement site location. Type: string, e.g. ``"Berlin"``.
- **Longitude**: Geographic longitude in decimal degrees. Type: float
	(comma as decimal separator is supported). Example: ``13,384714``.
- **Latitude**: Geographic latitude in decimal degrees. Type: float. Example:
	``52,542598``.
- **Height_asl**: Height above sea level in meters. Type: float. Example:
	``45,000000``.
- **working_directory**: Output directory for generated files. Type: string
	(path). Example: ``"D:\\Licel_TCPIP_Python\\data"``.
- **first_letter**: Prefix used for filenames when saving data. Type: string;
	example: ``"EH"``.
- **Zenith**: Zenith angle for the measurement (degrees). Type: float.
- **Azimuth**: Azimuth angle (degrees). Type: float.
- **frequency1/2/3**: Laser repetition frequencies in Hz. Type: float.


Section: ``[SP32]``
--------------------------

The following options are read by :class:`Licel.licel_SP32_Config.SP32_Config`
and stored in the ``SP32param`` attribute of the configuration object.

- **Discriminator**: Discriminator level for the channels. the valid range are 0–63. 
- **NoBins**: Number of bins (channels) per trace. ranges between 0 ... 32000 for high resolution mode (binwidth < 10ns)
	and between 0 ... 16000 for standard resolution mode (binwidth > 10ns)
- **Binwidth_ns**: Time resolution in nanoseconds (e.g. ``0,625`` for
	0.625 ns). 
- **HV**: Target high-voltage for the photomultiplier (Volts). 
- **centralWavelength**: Central wavelength of the spectrometer in nm. 
    represents the wavelength between channel 15 and channel 16 of the detector. 
- **nm_PerChannel**: Wavelength per channel (nm/channel) — used to derive
	spectral scaling. 



