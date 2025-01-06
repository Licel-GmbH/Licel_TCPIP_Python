#! python3.10
'''
Copyright ©: Licel GmbH

python sampleAcquis.py --ip <ip> --port <port> --device <Tr address> --memory <memory>
                    --bins <number of bins to read> --sqd_bins <number of sqd bins to read>
                    --range 100mV --squared|no-squared
'''
from Licel import  licel_data,licel_tcpip, licel_Config
import time 
import numpy
import argparse


def setMeasurmentInfo():
    
    MeasurmentInfo = licel_Config.MeasureInfo
    MeasurmentInfo.szLocation = "Berlin"      #measurement site
    MeasurmentInfo.nAltitude  = 45.000000     #the altitude above sea level
    MeasurmentInfo.dLongitude = 13.384714     # the longitude 11 digits (including - sign), six decimal places
    MeasurmentInfo.dLatitude  = 52.542598     #the latitude (11 digits (including - sign), six decimal places)
    MeasurmentInfo.Zenith     =  1.0          #the zenith angle (four digits in degrees), one decimal place) 
    MeasurmentInfo.Azimuth    = 15.000000     #the azimuth angle (four digits in degrees), one decimal place)
    MeasurmentInfo.repRateL0  = 10 
    MeasurmentInfo.repRateL1  = 10
    MeasurmentInfo.repRateL2  = 10
    
    return MeasurmentInfo

def saveDataToFile( filename, TRType, inputRange, shots, dmVData, datatype):
    header =( "ADC bits : {:d} \r\n Input Range : {:s} \r\n total shots : {:d}\r\n {:s}"
             .format(TRType['ADC Bits'], inputRange, shots, datatype))
    numpy.savetxt(filename, dmVData, header=header, newline='\r\n')

def commandLineInterface():
    argparser = argparse.ArgumentParser(description='sample acquisition example')
    argparser.add_argument('--ip', type=str, default = "10.49.234.234",
                            help='ethernet controller ip address')
    argparser.add_argument('--port', type=int, default=2055,
                            help='ethernet controller command port')
    argparser.add_argument('--device', type=int, default=0,
                            help='transient recorder address')
    argparser.add_argument('--memory', type=str,  default="MEM_A",
                            help='memory to acquire data from')
    argparser.add_argument('--squared', type=bool, default=False,
                            action=argparse.BooleanOptionalAction,
                            help='acquire squared data')
    argparser.add_argument('--bins', type=int, default=16000,
                            help='number of bins to read')
    argparser.add_argument('--sqd_bins', type=int, default=4000,
                            help='number of squared bins to read')
    argparser.add_argument('--range', type=str, default = "100mV",
                            help= ('transient recorder input range. possible values:'
                                   '20mV, 100mV, 500mV'))
    args = argparser.parse_args()
    return args 

def main():

    #initialize acquisition parameters using parameters passed from command line interface
    myArguments = commandLineInterface()    
    ip = myArguments.ip
    port = myArguments.port
    device = myArguments.device 
    memory = myArguments.memory
    DOSQUARE = myArguments.squared
    bins = myArguments.bins
    binsSqd = myArguments.sqd_bins
    inputRange = "-"+myArguments.range

    ethernetController = licel_tcpip.EthernetController (ip, port)
    dataParser = licel_data.DataParser()

    ethernetController.openConnection()
    print(ethernetController.getID())
    print(ethernetController.getCapabilities())
    installedTr = ethernetController.listInstalledTr()
    print(installedTr)
    ethernetController.selectTR(0)
    TRType = ethernetController.Tr.TRtype()
    print("TR Info : ", TRType, " \r\n")

    # Configure acquisition 
    print(ethernetController.Tr.setInputRange(inputRange))
    print(ethernetController.Tr.setThresholdMode("ON"))
    print(ethernetController.Tr.setDiscriminatorLevel(8))
    print(ethernetController.Tr.setMaxShots(4094))

    # start the acquisition 
    print(ethernetController.Tr.startAcquisition())
    time.sleep(1) 
    print(ethernetController.Tr.stopAcquisition()) # stop the Transient recorder 
    print(ethernetController.Tr.waitForReady(400)) # wait until the TR returns to the idle state

    acquisitionState, recording, mem,shots =ethernetController.Tr.getStatus()
    print("Shots Acquired : ", shots)

    # Get analogue raw data
    combinedAnalogueRawData, iClipping = ethernetController.Tr.getCombinedRawAnalogueData(TRType,
                                                                    dataParser,
                                                                    bins,
                                                                    shots,
                                                                    device,
                                                                    memory)

    dNormalized=dataParser.normalizeData(combinedAnalogueRawData, bins, shots)
    dmVData = dataParser.scaleAnalogData(dNormalized,inputRange, TRType)

    saveDataToFile("analogueData.txt",
                    TRType,
                    inputRange,
                    shots,
                    dmVData,
                    "analogue data in mV")
    print ("*** Saved dmVData ***")
  
    # Get analogue raw squared data
    if DOSQUARE :
        
        analogueSqdRawData = ethernetController.Tr.getCombinedRawAnalogueSquaredData(dataParser,
                                                                    binsSqd,
                                                                    device,
                                                                    memory) 
        
        sqd_bin = dataParser.getSquareRootBinary(combinedAnalogueRawData,
                                                 analogueSqdRawData,
                                                 binsSqd,
                                                 shots)
        
        SampleStandardDev = dataParser.normalizeSquaredData(sqd_bin, shots)
        meanErrorBinary = dataParser.meanError(SampleStandardDev, shots)
        meanError_mV = dataParser.scaleAnalogData(meanErrorBinary, inputRange, TRType)

        saveDataToFile("analogueSqdData.txt",
                        TRType,
                        inputRange,
                        shots,
                        meanError_mV,
                        "analogue mean error in mV")
        print ("*** Saved meanError_mV ***")



    # Get photon counting data 
    #TODO FIX PHOTON COUNTING DATA

    photonCountRawData = ethernetController.Tr.getRawPhotonCountingData(TRType,
                                                       dataParser,
                                                       bins,
                                                       shots,
                                                       device,
                                                       memory)
    
    dNormalized_PhotonCount = dataParser.normalizeData(photonCountRawData,bins, shots)
    dMHzData = dataParser.scale_PhotonCounting(dNormalized_PhotonCount, TRType['binWidth'])
    
    saveDataToFile("photon.txt",
                    TRType,
                    inputRange,
                    shots,
                    dMHzData,
                    "Photon Counts Data (counts per bin)")
    print ("*** Saved dMHz Data ***")
    
    # Get photon counting squared data 
    if DOSQUARE :

        squared_photon_data = ethernetController.Tr.getRawPhotonCountingSquaredData(dataParser,
                                                                   binsSqd,
                                                                   device,
                                                                   memory)

        sqd_bin = dataParser.getSquareRootBinary(photonCountRawData,
                                                 squared_photon_data,
                                                 binsSqd,
                                                 shots)

        SampleStandardDev = dataParser.normalizeSquaredData(sqd_bin,shots)

        meanErrorBinary = dataParser.meanError(SampleStandardDev, shots)

        saveDataToFile("photonSQD.txt",
                        TRType,
                        inputRange,
                        shots,
                        meanErrorBinary,
                        "Photon Counts mean Error Binary")
        print ("*** Saved meanErrorBinary ***")

    ethernetController.shutdownConnection()

if __name__ == "__main__":
    main()