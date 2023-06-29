#! python3.10

from Licel import licel_tr_tcpip, licel_data
import time 
import numpy

TR = 0 
DOSQUARE = True

IP = "127.0.0.1"
PORT = 2055 

acquisitionState =False
recording = False
memory = " "


def main():
    Rack = licel_tr_tcpip.licelTrTCP (IP, PORT)
    dataParser = licel_data.Data()

    Rack.openConnection()
    print(Rack.getID())
    print(Rack.selectTR(TR))

    TRType = Rack.TRtype()
    print("TR Info : ", TRType, " \r\n")
    print(Rack.setInputRange('-100mV'))
    print(Rack.setThresholdMode("ON"))
    print(Rack.setDiscriminatorLevel(4))
    print(Rack.setMaxShots(4094))

    print(Rack.startAcquisition())
    time.sleep(5) 
    print(Rack.stopAcquisition())
    print(Rack.waitForReady(2000))

    acquisitionState, recording, memory,shots =Rack.getStatus()
    print("Shots Acquired : ", shots)

    iNumber = 13000  #read a 13000 bin long trace
    iNumberSqd = 4000 # 4000 is the maximum bin length for squared data

    # Get analogue data
    if TRType['ADC Bits'] == 16 :
        mem_low_buffer  = Rack.getDataSet(TR, iNumber + 1, "LSW", "MEM_A")   
        mem_high_buffer = Rack.getDataSet(TR, iNumber + 1, "MSW", "MEM_A")
        mem_low   = numpy.frombuffer(mem_low_buffer,numpy.uint16)
        mem_high  = numpy.frombuffer(mem_high_buffer,numpy.uint16)
        mem_extra = numpy.zeros((iNumber))
        if shots > 4096 :
            mem_extra_buffer = Rack.getDataSet(TR, iNumber + 1,"PHM", "MEM_A")
            mem_extra = numpy.frombuffer(mem_extra_buffer,numpy.uint16)
        analogueRawData,iClipping = dataParser.combine_Analog_Datasets_16bit(mem_low, mem_high, mem_extra)
    else : 
        mem_low_buffer  = Rack.getDataSet(TR, iNumber + 1, "LSW", "MEM_A")   
        mem_high_buffer = Rack.getDataSet(TR, iNumber + 1, "MSW", "MEM_A")
        mem_low  = numpy.frombuffer(mem_low_buffer,numpy.uint16)
        mem_high = numpy.frombuffer(mem_high_buffer,numpy.uint16)
        analogueRawData,iClipping = dataParser.combine_Analog_Datasets(mem_low, mem_high)


    dNormalized=dataParser.normalizeData(analogueRawData, iNumber, shots)
    dmVData = dataParser.scaleAnalogData(dNormalized,'-100mV', TRType)
    dataParser.plot(dmVData,"dmVData_Analogue", "bins", "mV")

    clipped_bin_count = numpy.count_nonzero(iClipping)
    if clipped_bin_count :
        clipping_detected = True
        print("clippped_bin_count : ",clipped_bin_count)
    
    # Get analogue squared data
    if DOSQUARE :
        
        mem_low_buffer   = Rack.getDataSet(TR, iNumberSqd + 1, "A2L", "MEM_A") 
        mem_high_buffer  = Rack.getDataSet(TR, iNumberSqd + 1, "A2M", "MEM_A")
        mem_extra_buffer = Rack.getDataSet(TR, iNumberSqd + 1, "A2H", "MEM_A") 
        mem_low   = numpy.frombuffer(mem_low_buffer, numpy.uint16)
        mem_high  = numpy.frombuffer(mem_high_buffer, numpy.uint16)
        mem_extra = numpy.frombuffer(mem_extra_buffer, numpy.uint16)

        analogueSqdRawData = dataParser.combineAnalogSquaredData(mem_low, mem_high, mem_extra)

        sqd_bin = dataParser.getSquareRootBinary(analogueRawData, analogueSqdRawData, iNumberSqd, shots)
        SampleStandardDev = dataParser.normalizeSquaredData(sqd_bin, shots)
        dataParser.plot(SampleStandardDev, "dSampleStandardDev_Analogue", "bins", "mV")

        meanErrorBinary = dataParser.meanError(SampleStandardDev, shots)
        meanError_mV = dataParser.scaleAnalogData(meanErrorBinary, '-100mV', TRType)
        dataParser.plot(meanError_mV, "meanError_mV_Analogue", "bins", "mV")

    # Get photon counting data 
    if((TRType['PC Bits'] == 4  and shots > 4096) or 
    (TRType['PC Bits'] == 6 and shots > 1024) or 
    (TRType['PC Bits'] == 8 and shots > 256)) :
        mem_low_buffer   = Rack.getDataSet(TR, iNumber + 1, "PC" , "MEM_A") 
        mem_extra_buffer = Rack.getDataSet(TR, iNumber + 1 , "PHM", "MEM_A") 
        mem_low   = numpy.frombuffer(mem_low_buffer,numpy.uint16)
        mem_extra = numpy.frombuffer(mem_extra_buffer,numpy.uint16)
        photonCountRawData = dataParser.convert_Photoncounting_Fullword(mem_low, mem_extra)

    else: 
        PUREPHOTON = 0
        mem_low_buffer   = Rack.getDataSet(TR, iNumber + 1, "PC" , "MEM_A") 
        mem_low   = numpy.frombuffer(mem_low_buffer,numpy.uint16)
        photonCountRawData = dataParser.convert_Photoncounting(mem_low, PUREPHOTON)


    dNormalized_PhotonCount = dataParser.normalizeData(photonCountRawData,iNumber, shots)

    dMHzData = dataParser.scale_PhotonCounting(photonCountRawData, TRType['binWidth'])
    dataParser.plot(dMHzData, "dMHzData", "bins", "MHZ")    

    # Get photon counting squared data 
    if DOSQUARE :
        mem_low_buffer   = Rack.getDataSet(TR, iNumberSqd + 1, "P2L", "MEM_A") 
        mem_high_buffer  = Rack.getDataSet(TR, iNumberSqd + 1, "P2M", "MEM_A")
        mem_low   = numpy.frombuffer(mem_low_buffer,numpy.uint16)
        mem_high  = numpy.frombuffer(mem_high_buffer,numpy.uint16)

        squared_photon_data = dataParser.combine_Photon_Squared_Data(mem_low, mem_high)
        dataParser.plot(squared_photon_data, "squared_photon_data", "bins", "MHZ")    

        sqd_bin = dataParser.getSquareRootBinary(photonCountRawData, squared_photon_data, iNumberSqd, shots)

        SampleStandardDev = dataParser.normalizeSquaredData(sqd_bin,shots)
        dataParser.plot(SampleStandardDev, "SampleStandardDev_photon", "bins", "MHZ")    

        meanErrorBinary = dataParser.meanError(SampleStandardDev, shots)
        dataParser.plot(meanErrorBinary, "meanErrorBinary_photon", "bins", "MHZ")    

    Rack.shutdownConnection()

if __name__ == "__main__":
    main()