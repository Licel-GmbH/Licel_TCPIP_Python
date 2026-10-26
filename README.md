# **Licel_TCPIP Python**  

**The Licel_TCPIP python library was developed and tested with python 3.10.11 .** 

**running this library with python version 3.8 will result in error** 

# **Documentation** 
**The Python library documentation is to be found under:**
https://licel-gmbh.github.io/Licel_TCPIP_Python/

**Detailed manuals are to be found under:**
https://licel.com/soft_man.html

## Installing requirements: 
```shell
pip install -r requirements.txt
```

## run sampleAcquis.py example : 
```shell
python sampleAcquis.py --ip <ip> --port <port> --device <Tr address> --memory <memory>
                    --bins <number of bins to read> --sqd_bins <number of sqd bins to read>
                    --range 100mV --squared|no-squared
```

The sampleAcquis.py will acquire data through command socket and save data respectively to 
analogueData.txt, analogueSqdData.txt, photon.txt and photonSQD.txt  

**Manual:** [Transient recorder user manual](https://licel.com/manuals/TR40-16bit3U_Manual.pdf)


## run powermeter_example.py : 
```shell
python3 powermeter_example.py --ip <ip> --port <port>  --acq <num acquis> --channel <channel>
```

the powermeter_example.py will demonstrate the use of the push acquistion as well as the 
single trace acquisition. 

**Manual:** [Power Meter user manual](https://licel.com/manuals/Powermeter.pdf)

## run pmt_example.py : 
```shell
python3 pmt_example.py --ip <ip> --port <port> --device <device address> --voltage <voltage>
```

the pmt_example.py demonstrate how to list all installed pmt, set and read voltage from a selected device

**Manual:** [PMT user manual](https://licel.com/manuals/pmtmanual.pdf),
[PMT + Quad HV user manual](https://licel.com/manuals/pmtmanual_QuadHV.pdf) or
[Gated PMT user manual](https://licel.com/manuals/pmtmanualgating.pdf), depending on your PMT module

## run mpush_example.py :
```shell
python3 mpush_example.py --ip <ip> --port <port>  --acq <num acquis> --shots <num shots>
                 --acquis_per_file <acquis per file> --log
```

mpush_example.py demonstrate the use of mpush mode to read multiple datasets from multiple transient recorders, at the same time. 

**Manual:** [Transient recorder user manual](https://licel.com/manuals/TR40-16bit3U_Manual.pdf),
the saved files are described in the [file format description](https://licel.com/raw_data_format.html)

## run waverider_example.py :
```shell
python3 waverider_example.py --ip <ip> --port <port> --shots <shots> 
                        --fft_size <fft_size> --range <range> 
```

waverider_example.py shows how to configure the Waverider, collect power spectrum data,
and save the data in a NETCDF file.

**Manual:** [Waverider User Manual 400MHz](https://licel.com/manuals/WaveriderManual.pdf) or
[Waverider User Manual Quad 250MHz](https://licel.com/manuals/WaveriderManual_Quad.pdf), depending on your Waverider

## run SP32_example.py :
```shell
python3 SP32_example.py --ip <ip> --port <port> --shots <num shots> --acq <num acquis> --sim <0|1>
```

SP32_example.py configures the SP32 from SP32.ini, then acquires and saves data. `--sim 1` uses the internal trigger.

**Manual:** [SP32 user manual](https://licel.com/manuals/SP32_Manual.pdf) or
[SP32HR user manual](https://licel.com/manuals/SP32HR_Manual.pdf), depending on your detector

## run SilentStat_Runtime_example.py :
```shell
python3 SilentStat_Runtime_example.py --ip <ip> --port <port> --on|--off
                 --preTrigDelay <us> --postTrigDelay <us>
```

SilentStat_Runtime_example.py turns SilentStat on or off and sets its delays, without saving them to flash.

**Manual:** [Ethernet Manual](https://licel.com/manuals/ethernet_pmt_tr.pdf)

## run SilentStat_Store_example.py :
```shell
python3 SilentStat_Store_example.py --ip <ip> --port <port> --password <password>
```

SilentStat_Store_example.py saves the current SilentStat configuration to flash (default password 'Administrator').

**Manual:** [Ethernet Manual](https://licel.com/manuals/ethernet_pmt_tr.pdf)

## run timing_example.py :
```shell
python3 timing_example.py
```

timing_example.py sets the trigger timing and mode of each channel from Timing.ini. ip and port are set in the script.

**Manual:** [Trigger Timing Controller user manual](https://licel.com/manuals/GatingTrigger.pdf)

## run laserSync_example.py :
```shell
python3 laserSync_example.py
```

laserSync_example.py applies the Laser Sync configuration from Timing.ini and saves it to flash. ip and port are set in the script.

**Manual:** [Laser Sync Controller user manual](https://licel.com/manuals/LaserSync.pdf)

## run SearchControllers.py :
```shell
python3 SearchControllers.py
```

SearchControllers.py lists the Licel Ethernet controllers found on the local network.

**Manual:** [Ethernet Manual](https://licel.com/manuals/ethernet_pmt_tr.pdf),
[Licel Ethernet Controller - Debugging the network setup](https://licel.com/manuals/debug1.pdf)

## run setDHCP.py :
```shell
python3 setDHCP.py <old ip> <old port> <new port> <password> [--dry-run]
```

setDHCP.py switches the controller to DHCP. `--dry-run` only prints the command.

**Manual:** [Ethernet Manual](https://licel.com/manuals/ethernet_pmt_tr.pdf)

## run setfixed.py :
```shell
python3 setfixed.py <old ip> <old port> <new ip> <new port> <mask> <gateway> <password> [--dry-run]
```

setfixed.py sets a fixed ip address on the controller. `--dry-run` only prints the command.

**Manual:** [Ethernet Manual](https://licel.com/manuals/ethernet_pmt_tr.pdf)
