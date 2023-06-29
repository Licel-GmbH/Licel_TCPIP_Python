import numpy 
from matplotlib import pyplot as plt
from Licel import licel_tr_tcpip
import math 

class Data:
    
    def __init__(self) -> None:
        return 

    def checkDelimiter(self,data) -> list[int]:
        '''
        return a list holding the positions of "\\xff\\xff" delimiter  
        last element of the returned list is -1 indecating that the delimiter is not found.

        '''
        temp= 0
        delimiterPos = []
        while True:
            temp = data.find(b'\xff\xff',temp,len(data))   
            delimiterPos.append(temp)              
            if temp == -1:
                return delimiterPos
            temp += 2
        return 
    
    def combine_Analog_Datasets_16bit(self, uLSW, uMSW, uPHM):
        '''
        Converts the LSW and the MSW values into an int32 numpy array containing the
        summed up analog values.
        '''
        lAccumulated = numpy.zeros((uLSW.size), numpy.uint32)
        iClipping    = numpy.zeros((uLSW.size), numpy.uint32)
        uMSW__ = uMSW.astype(numpy.uint32,casting='unsafe')
        uLSW__ = uLSW.astype(numpy.uint32,casting='unsafe')
        uPHM__ = uPHM.astype(numpy.uint32,casting='unsafe')
        sMSW__ = uMSW.astype(numpy.int16,casting='unsafe')
        for i in range(1,uLSW.size):
            lAccumulated [i-1] = uLSW__[i] + ((uMSW__[i] & 0x0fff) << 16) +((uMSW__[i] & 0xE000) << 15) 
            iClipping    [i-1] = ((sMSW__[i] & 0x1000) >> 12)
            if  not (numpy.all(uPHM__ == 0 )) :
                lAccumulated [i-1] += (uPHM__[i] & 0x0100) << 23 
        return lAccumulated.astype(numpy.uint32,casting='unsafe'), iClipping.astype(numpy.uint32,casting='safe') 
    

    def combine_Analog_Datasets(self, uLSW, uMSW):
        lAccumulated = numpy.zeros((uLSW.size), numpy.uint32)
        iClipping    = numpy.zeros((uLSW.size), numpy.uint32)
        uMSW = uMSW.astype(numpy.uint32,casting='unsafe')
        uLSW = uLSW.astype(numpy.uint32,casting='unsafe')
        sMSW = uMSW.astype(numpy.int16,casting='unsafe')
        for i in range(0,uLSW.size):
            lAccumulated [i] = uLSW[i+1] + ((uMSW[i+1] & 0xff) << 16) 
            iClipping    [i] = ((sMSW[i+1] & 0x100) >> 8)
        return  lAccumulated.astype(numpy.uint32,casting='unsafe'), iClipping.astype(numpy.uint32,casting='safe') 

    def normalizeData (self,data ,iNumber,iShots ):
        dNormalized  = numpy.zeros((iNumber),numpy.double)
        shots = iShots
        if shots == 0:
            shots = 1 
        for i in range(0,iNumber):
            dNormalized[i] = data[i]/shots
        return dNormalized

    def scaleAnalogData(self,dNormalized, inputRange, TRType ):
        dScale = 1
        if licel_tr_tcpip.INPUTRANGE[inputRange] == 0 :
            dScale = 500 / (1 << TRType['ADC Bits'])
        elif licel_tr_tcpip.INPUTRANGE[inputRange] == 1 :
            dScale = 100 / (1 << TRType['ADC Bits'])
        elif licel_tr_tcpip.INPUTRANGE[inputRange] == 2 :
            dScale = 20 / (1 << TRType['ADC Bits'])
        return  (dNormalized * dScale)

    def combineAnalogSquaredData(self,uSQLSW, uSQMSW, uSQHSW):
        llSQAccumulated  = numpy.zeros((uSQMSW.size),numpy.uint64)
        uSQMSW__ = numpy.asarray(uSQMSW,numpy.uint)
        uSQLSW__ = numpy.asarray(uSQLSW,numpy.uint)
        uSQHSW__ = numpy.asarray(uSQHSW,numpy.uint)
        for i in range(1, uSQMSW.size):
            llSQAccumulated[i-1] = uSQLSW__[i] + (uSQMSW__[i] << 16 ) + (uSQHSW__[i] << 32)
        return llSQAccumulated.astype(numpy.uint64, casting='safe')

    def getSquareRootBinary (self, data, squaredData, iNumber, iShots ):
        lAccumulated_bis = data.astype(numpy.uint64,casting='unsafe')
        sqd_bin = numpy.zeros((iNumber), numpy.uint32)
        temp = 0
        y = 0
        for i in range (0, iNumber):
            temp = (squaredData[i] * iShots) - (lAccumulated_bis[i] * lAccumulated_bis[i])
            y = math.sqrt(temp) - 0.000001
            if (2*y < temp - y**2 ):
                y += 1 
            sqd_bin [i] = int(y)
        return sqd_bin
    
    def normalizeSquaredData(self,sqd_bin,iShots):
        divider = math.sqrt(iShots*(iShots-1)) if (iShots > 1) else 1
        dSampleStandardDev = sqd_bin / divider
        return dSampleStandardDev

    def meanError(self,sampleStdDev, iShots):
        divider = math.sqrt(iShots) if (iShots > 1) else 1
        meanError = sampleStdDev / divider
        return meanError

    def convert_Photoncounting_Fullword(self, uPHO, uPHM):
        photon_c  = numpy.zeros((uPHO.size),numpy.uint32)
        uPHO = uPHO.astype(numpy.uint32,casting='unsafe')
        uPHM = uPHM.astype(numpy.uint32,casting='unsafe')
        for i in range(1,uPHO.size):
            photon_c[i-1] = uPHO[i] + ((uPHM[i] & 0xFF) <<16 )
        return photon_c

    def convert_Photoncounting(self, uPHO, iPurePhoton):
        photon_c  = numpy.zeros((uPHO.size),numpy.uint32)
        iMask = 0x7FFF
        if (iPurePhoton):
            iMask = 0xFFFF
        photon_c = uPHO & iMask
        return photon_c

    def scale_PhotonCounting(self, photonCount, binWidth):
        scaled_photon_c  = numpy.zeros((photonCount.size),numpy.double)
        dScale = 150 / binWidth
        scaled_photon_c = dScale * photonCount
        return scaled_photon_c
    
    def combine_Photon_Squared_Data(self, uSQLSW, uSQMSW):
        squared_photon_data  = numpy.zeros((uSQLSW.size),numpy.uint64)
        uSQLSW__ = numpy.asarray(uSQMSW,numpy.uint)
        uSQMSW__ = numpy.asarray(uSQLSW,numpy.uint)
        for i in range(1, uSQLSW.size):
            squared_photon_data[i-1] = uSQLSW__[i] + (uSQMSW__[i] << 16 )
        return squared_photon_data
        

    def plot(self, data, titel, x_caption, y_caption):
        plt.title(titel) 
        plt.xlabel(x_caption) 
        plt.ylabel(y_caption) 
        plt.plot(data) 
        plt.show()