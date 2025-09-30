'''
Copyright ©: Licel GmbH

Usage : 
python3 .\wind_example.py --ip <ip> --port <port> --shots <shots> 
                          --fft_size <fft_size> --range <range> 
'''

from Licel import  licel_tcpip, licel_wind, licel_netCDF
import argparse
import time
import numpy as np

# Acquisition parameters
runs = 4
num_trig = 1
samplingRate_hz = 250000000
# geographical position parameters
Altitude = 65
Longitude = 52.54255953597681 
Latitude = 13.384646763135557
azimuth = 23
zenith = 20



def commandLineInterface():
    argparser = argparse.ArgumentParser(description='waverider example ')
    argparser.add_argument('--ip', type=str, default = "10.49.234.234",
                            help='waverider ip address')
    argparser.add_argument('--port', type=int, default=2055,
                            help='waverider command port')
    argparser.add_argument('--shots', type=int,  default=1000,
                            help='number of shots per acquisition')
    argparser.add_argument('--fft_size', type=int,  default=32,
                            help="number of adc samples that goes into computing "
                            "one fft. Accepted values: 32,64,128,256,512,1024.")
    argparser.add_argument('--range', type=int,  default=15000,
                            help='Defines the maximum distance the ADC trace ' \
                            'should cover in meters. Max range is 39320 meters')

    args = argparser.parse_args()
    return args

#initialize acquisition parameters using parameters passed from command line interface
myArguments = commandLineInterface()
ip = myArguments.ip
port = myArguments.port
shots = myArguments.shots
FFT_Size = myArguments.fft_size
MaxRange_meter = myArguments.range 

def main():


    ethernetController = licel_tcpip.EthernetController(ip, port)
    waverider = licel_wind.Waverider(ethernetController)


    ethernetController.openConnection()

    print(waverider.getCAP())
    print(waverider.getID())
    print(waverider.getHWDescr())

    print(waverider.setShots(shots))
    print(waverider.getShotsSettings())

    print(waverider.setFFTsize(FFT_Size))
    print(waverider.getFFTsize())

    numFFT = waverider.getRangebins(MaxRange_meter,FFT_Size, samplingRate_hz)

    print(waverider.setNumFFT(numFFT))
    print(waverider.getNumFFT())

    waverider_NetCDF = licel_netCDF.Licel_Netcdf_Wrapper("filename.nc","w", "Waverider",
                                                     numFFT, FFT_Size, num_trig)
    
    waverider_NetCDF.fillGeoPositionInfo("Berlin", Latitude, Longitude,
                                     Altitude, azimuth, zenith )
    
    waverider_NetCDF.fillAcquisitionInfo(MaxRange_meter, samplingRate_hz,
                                         shots, FFT_Size, waverider )
    

    waverider_NetCDF.timestamp_start[:] = waverider.getMSEC()
    waverider_NetCDF.pc_time_start[:] = waverider_NetCDF.time_unix_to_epoch_1904()
    print("Starting Acquisition")
    cycle = 0
    while cycle < runs : 
        waverider.startAcq()
        dataAvailable = False 
        while dataAvailable == False: 
            dataAvailable = waverider.isDataAvailable() 
            time.sleep(1/1000) 

        timestamp, powerSpectra= waverider.getData(FFT_Size,numFFT)
        waverider_NetCDF.pc_time_read[:] = waverider_NetCDF.time_unix_to_epoch_1904()

        currentShots = waverider.getCurrentShots()

        waverider_NetCDF.saveNetcdf(cycle, powerSpectra, timestamp, currentShots)
        cycle = cycle + 1

if __name__ == "__main__":
    main()



    
