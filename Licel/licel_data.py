'''
Copyright ©: Licel Gmbh 

The data class holds method for (pre)processing the raw data,
displaying data with matplotlib and saving data to Licel file format
'''
import numpy 
from matplotlib import pyplot as plt
from Licel import licel_tr_tcpip
import math 
from datetime import datetime
import os

MPUSH_SHOTNUM_OFFSET = 2 # represents 2 byte shot number needed to parser MPUSH response
class DataParser:
    
    #: internal value to keep count for how many acquisition are 
    #:already written into a the actual file
    _acquisWrittenToFile : int = 0
    #:internal value to keep the file path, where dataset is to be saved, into memory, 
    #:``_path`` is updated by ``saveFile()`` if  ``_acquisWrittenToFile`` == ``ACQUISPERFILE``  
    _path : str  = " "

    def __init__(self) -> None:
        return 

    def _checkDelimiter(self, pushBuffer : bytearray) -> list[int]:
        """
        find the delimiter 'xff xff' positions in the pushBuffer.        

        :param pushBuffer: Buffer holding raw data acquired from push socket.\r\n
        :type pushBuffer: bytearray

        :return: list holding the positions of '\\xff \\xff' in the ``pushBuffer``.
                last element of the returned list is -1 indicating that we searched the
                totality of the ``pushBuffer``, '\\xff \\xff' is not more to be found.
        :rtype: list[int]
        """
        temp= 0
        delimiterPos = []
        while True:
            temp = pushBuffer.find(b'\xff\xff',temp,len(pushBuffer))   
            delimiterPos.append(temp)              
            if temp == -1:
                return delimiterPos
            temp += 2
        return 
    
    def combine_Analog_Datasets_16bit(self, uLSW, uMSW, uPHM):
        """
        Converts the ``uLSW``, ``uMSW``, ``uPHM`` values into an integer array containing the
            summed up analog values. The first trash element (due to the data transmission
            scheme) are also removed. 
            Used for transient recorder with 16bit ADC 

        :param uLSW: array holding memory low raw data as uint16   
        :type uLSW: numpy.ndarray(dtype=uint16, ndim =1)  

        :param uMSW: array holding memory High raw data as uint16   
        :type uMSW: numpy.ndarray(dtype=uint16, ndim =1)  

        :param uPHM: array holding memory extra raw data as uint16   
        :type uPHM: numpy.ndarray(dtype=uint16, ndim =1)  

        :return: list containing 2 numpy array: \r\n
            -the first array contains the summed up analog data. \r\n
            -the second array containing the clipping(out of range) information. \r\n 
            1 if the overange condition (for the specific data point) is at least  \r\n
            fulfilled once, otherwise 0. \r\n 

        :rtype: [numpy.ndarray(dtype=uint32, ndim =1), \r\n 
                 numpy.ndarray(dtype=uint32, ndim =1)]
        """
        lAccumulated = numpy.zeros((uLSW.size), numpy.uint32)
        iClipping    = numpy.zeros((uLSW.size), numpy.uint32)
        uMSW__ = uMSW.astype(numpy.uint32,casting='unsafe')
        uLSW__ = uLSW.astype(numpy.uint32,casting='unsafe')
        uPHM__ = uPHM.astype(numpy.uint32,casting='unsafe')
        sMSW__ = uMSW.astype(numpy.int16,casting='unsafe')
        lAccumulated  = uLSW__ + ((uMSW__ & 0x0fff) << 16) +((uMSW__ & 0xE000) << 15) 
        iClipping     = ((sMSW__ & 0x1000) >> 12)
        if  not (numpy.all(uPHM__ == 0 )) :
            lAccumulated  += (uPHM__ & 0x0100) << 23 
        #remove non valid first array element. 
        return numpy.delete(lAccumulated,0), iClipping.astype(numpy.uint32,casting='unsafe') 
    
    def combine_Analog_Datasets(self, uLSW, uMSW):
        '''
        Converts the ``uLSW``, ``uMSW`` values into an integer array containing the
        summed up analog values. The first trash element (due to the data transmission
        scheme) are also removed. \r\n
        Used for transient recorder with 12bit ADC 
        
        :param uLSW: array holding memory low raw data as uint16   
        :type uLSW: numpy.ndarray(dtype=uint16, ndim =1)  

        :param uMSW: array holding memory High raw data as uint16   
        :type uMSW: numpy.ndarray(dtype=uint16, ndim =1)  



        :return: list containing 2 numpy array: \r\n
                 -the first array contains the summed up analog data.\r\n
                 -the second array containing the clipping(out of range) information. 
                 1 if the overange condition (for the specific data point) is at least
                 fulfilled once, otherwise 0 
        :rtype: [numpy.ndarray(dtype=uint32, ndim =1), 
                 numpy.ndarray(dtype=uint32, ndim =1)]
        '''
        lAccumulated = numpy.zeros((uLSW.size), numpy.uint32)
        iClipping    = numpy.zeros((uLSW.size), numpy.uint32)
        uMSW = uMSW.astype(numpy.uint32,casting='unsafe')
        uLSW = uLSW.astype(numpy.uint32,casting='unsafe')
        sMSW = uMSW.astype(numpy.int16,casting='unsafe')
       
        lAccumulated  = uLSW + ((uMSW & 0xff) << 16) 
        iClipping     = ((sMSW & 0x100) >> 8)
        return  numpy.delete(lAccumulated,0), iClipping.astype(numpy.uint32,casting='unsafe') 

    def normalizeData(self,accumulatedData, iNumber, iShots):
        """
        Normalizes the accumulated Data with respect to the number of shots

        :param accumulatedData: numpy array holding accumulated analogue data.
        :type accumulatedData: numpy.ndarray(dtype=uint32, ndim =1) 

        :param iNumber: number of bins. 
        :type iNumber: uint 

        :param iShots: number of shots. 
        :type iShots: uint

        :returns: normalized data. 
        :rtype: numpy.ndarray(dtype=double, ndim =1)
        """
        dNormalized  = numpy.zeros((iNumber),numpy.double)
        shots = iShots
        if shots == 0:
            shots = 1 
        dNormalized = accumulatedData/shots
        return dNormalized

    def scaleAnalogData(self,dNormalized, inputRange, TRHardwareInfo):
        """
        Scales the normalized data with respect to the input range. 

        :param dNormalized: normalized data. 
        :type dNormalized: numpy.ndarray(dtype=double, ndim =1)

        :param inputRange: input range possible values are: '-500mV' '-100mV' '-20mV'
        :type inputRange: str

        :param TRHardwareInfo: holds information about transient hardware info
        :type TRHardwareInfo: dict{'ADC Bits' : ' ', 'PC Bits' : ' ' , 'FIFOLength': ' ' ,
                           'binWidth' : ' ','ID' : ' ', 'HWCAP' : ' ', 'binShift': ' ',
                           'raw': ' '} 

        :returns: scaled data 
        :rtype: numpy.ndarray(dtype=double, ndim =1)
        """
        dScale = 1
        if licel_tr_tcpip.INPUTRANGE[inputRange] == 0 :
            dScale = 500 / (1 << TRHardwareInfo['ADC Bits'])
        elif licel_tr_tcpip.INPUTRANGE[inputRange] == 1 :
            dScale = 100 / (1 << TRHardwareInfo['ADC Bits'])
        elif licel_tr_tcpip.INPUTRANGE[inputRange] == 2 :
            dScale = 20 / (1 << TRHardwareInfo['ADC Bits'])
        return  (dNormalized * dScale)

    def combineAnalogSquaredData(self,uSQLSW, uSQMSW, uSQHSW):
        """
        Converts the ``uSQLSW``, ``uSQMSW``, ``uSQHSW`` values into an integer array 
        containing the squared up analogue values. The first trash element 
        (due to the data transmission scheme) are also removed. 

        :param uSQLSW: array holding memory low raw data as uint16  
        :type uSQLSW:  numpy.ndarray(dtype=uint16, ndim =1)  

        :param uSQMSW: array holding memory high raw data as uint16  
        :type uSQMSW:  numpy.ndarray(dtype=uint16, ndim =1)  

        :param uSQHSW: array holding memory extra raw data as uint16    
        :type uSQHSW:  numpy.ndarray(dtype=uint16, ndim =1)  

        :returns: accumulated squared data 
        :rtype: numpy.ndarray(dtype=uint64, ndim =1)  
         """
        llSQAccumulated  = numpy.zeros((uSQMSW.size),numpy.uint64)
        uSQMSW__ = numpy.asarray(uSQMSW,numpy.uint)
        uSQLSW__ = numpy.asarray(uSQLSW,numpy.uint)
        uSQHSW__ = numpy.asarray(uSQHSW,numpy.uint)
        for i in range(1, uSQMSW.size):
            llSQAccumulated[i-1] = uSQLSW__[i] + (uSQMSW__[i] << 16 ) + (uSQHSW__[i] << 32)
        return llSQAccumulated.astype(numpy.uint64, casting='safe')

    def getSquareRootBinary (self, combinedAnalogueRawData, combinedSqdData, iNumber, iShots ):
        """
        Convert the squared data to binary number for the std dev. 

        :param combinedAnalogueRawData: holds the combined analogue raw data
        :type combinedAnalogueRawData: numpy.ndarray(dtype=uint32, ndim =1)

        :param combinedSqdData: holds the combined squared data.
        :type combinedAnalogueRawData: numpy.ndarray(dtype=uint64, ndim =1)

        :param iNumber : number of bins. 
        :type iNumber: uint 

        :param iShots: number of shots
        :type iShots: uint 

        :returns: square root of  ( ``combinedSqdData`` * ``iShots`` ) - ( ``combinedAnalogueRawData`` ^ 2 ) \r\n
        :rtype: numpy.ndarray(dtype=uint32, ndim =1)
 
        """
        lAccumulated_bis = combinedAnalogueRawData.astype(numpy.uint64,casting='unsafe')
        sqd_bin = numpy.zeros((iNumber), numpy.uint32)
        temp = 0
        y = 0
        for i in range (0, iNumber):
            temp = (combinedSqdData[i] * iShots) - (lAccumulated_bis[i] * lAccumulated_bis[i])
            y = math.sqrt(temp) - 0.000001
            if (2*y < temp - y**2 ):
                y += 1 
            sqd_bin [i] = int(y)
        return sqd_bin
    
    def normalizeSquaredData(self,sqd_bin,iShots):
        """
        Normalizes the squared Data with respect to the number of shot

        :param sqd_bin: square root binary data 
        :type: numpy.ndarray(dtype=uint32, ndim =1)

        :param iShots: number of shots. 
        :type iShots: uint 

        :returns: the sample standard deviation. 
        :rtype:  numpy.ndarray(dtype=double, ndim =1)
        """
        divider = math.sqrt(iShots*(iShots-1)) if (iShots > 1) else 1
        dSampleStandardDev = sqd_bin / divider
        return dSampleStandardDev

    def meanError(self,sampleStdDev, iShots):
        """
        convert the sample standard devition to the more relevant error of the mean value.

        :param sampleStdDev: the sample standard deviation.
        :type sampleStdDev: numpy.ndarray(dtype=double, ndim =1)

        :param iShots: number of shots. 
        :type iShots: uint 

        :returns: error of the mean value 
        :rtype: numpy.ndarray(dtype=double, ndim =1)  
        """
        divider = math.sqrt(iShots) if (iShots > 1) else 1
        meanError = sampleStdDev / divider
        return meanError

    def convert_Photoncounting_Fullword(self, uPHO, uPHM):
        """
        Converts the raw Photon counting data into an integer array containing the
        summed up photon counting values. The first trash element (due to the data
        transmission scheme) are also removed. 
        to be used if 
        (PC Bits == 4  and shots > 4096 or 
        PC Bits == 6  and shots > 1024 or 
        PC Bits == 8  and shots > 256)

        :param uPHO: memory low buffer 
        :type uPHO: numpy.ndarray(dtype=uint16, ndim =1)  

        :param uPHM: memory extra buffer 
        :type uPHM: numpy.ndarray(dtype=uint16, ndim =1)  

        :returns: photon counting raw data 
        :rtype: numpy.ndarray(dtype=uint32, ndim =1)
        """
        photon_c  = numpy.zeros((uPHO.size),numpy.uint32)
        uPHO = uPHO.astype(numpy.uint32,casting='unsafe')
        uPHM = uPHM.astype(numpy.uint32,casting='unsafe')
        for i in range(1,uPHO.size):
            photon_c[i-1] = uPHO[i] + ((uPHM[i] & 0xFF) <<16 )
        return numpy.delete(photon_c,0)

    def convert_Photoncounting(self, uPHO, iPurePhoton):
        """
        Converts the  raw Photon counting data into an integer array containing the
        summed up photon counting values. The first trash element (due to the data
        transmission scheme) are also removed. The clipping information present in the
        most significant bit is masked out if neccessary

        :param uPHO: memory low buffer 
        :type uPHO: numpy.ndarray(dtype=uint16, ndim =1)  

        :param iPurePhoton: mask clipping information if 1 
        :type iPurePhoton: uint

        :returns: photon counting raw data 
        :rtype: numpy.ndarray(dtype=uint32, ndim =1)
        """
        photon_c  = numpy.zeros((uPHO.size),numpy.uint32)
        iMask = 0x7FFF
        if (iPurePhoton):
            iMask = 0xFFFF
        photon_c = uPHO & iMask
        return numpy.delete(photon_c,0)

    def scale_PhotonCounting(self, normalizedPhotonCount, binWidth):
        """
        Scales the normalized photon counting data with respect to the bin width 

        :param normalizedPhotonCount: normalized photon counting data 
        :type normalizedPhotonCount: numpy.ndarray(dtype=double, ndim =1)

        :param binwidth: bin width in meter. 
        :type binwidth:  double 

        :returns: scaled photon counting data 
        :rtype: numpy.ndarray(dtype=double, ndim =1)
        """
        scaled_photon_c  = numpy.zeros((normalizedPhotonCount.size),numpy.double)
        dScale = 150 / binWidth
        scaled_photon_c = dScale * normalizedPhotonCount
        return scaled_photon_c
    
    def combine_Photon_Squared_Data(self, uSQLSW, uSQMSW):
        """
        combine squared photon raw data . 

        :param uSQLSW: raw data memory low buffer
        :type uSQLSW: numpy.ndarray(dtype=uint16, ndim =1)

        :param uSQMSW: raw data memory high buffer 
        :type uSQMSW: numpy.ndarray(dtype=uint16, ndim =1)

        :returns: combined squared photon data
        :rtype: numpy.ndarray(dtype=uint64, ndim =1) 
        """
        squared_photon_data  = numpy.zeros((uSQLSW.size),numpy.uint64)
        uSQLSW__ = numpy.asarray(uSQMSW,numpy.uint)
        uSQMSW__ = numpy.asarray(uSQLSW,numpy.uint)
        for i in range(1, uSQLSW.size):
            squared_photon_data[i-1] = uSQLSW__[i] + (uSQMSW__[i] << 16 )
        return squared_photon_data
        
    def plot(self, data, title, x_caption, y_caption):
        """
        display data using matplotlib

        :param data: data to be displayed :
            data could be analogue, photon counting, squared analogue and
            squared photon counting. data format could be raw, scaled or normalized..   
        
        :param data: data to be displayed. 
        :type data: numpy.ndarray()

        :param title: title of the graph to be displayed 
        :type: str 

        :param x_caption: x axis label 
        :type x_caption: str 

        :param y_caption: y axis label 
        :type x_caption: str
        """
        plt.title(title) 
        plt.xlabel(x_caption) 
        plt.ylabel(y_caption) 
        plt.plot(data) 
        plt.show()
    
    def removeInvalidDataFromBuffer(self, pushBuffer):
        '''
        remove raw data from buffer until next occurrence of xff xff. 
        this is used to clear the ```pushBuffer`` if the data is invalid. 
        in the example below we want to remove the first line containing invalid raw data
        until the next occurrence of the xff xff delimiter marking the start of new data set:\r\n
        1- <xff xff> <timestamp> <shots> <INVALID raw data> \r\n
        2- <xff xff> <timestamp><shots> <raw data> <xff xff>  

        we can use the function ``trimBuffer`` to delete invalid data from buffer 
        without affecting the next dataset 

        :param pushBuffer: buffer containing raw data
        :type pushBuffer: bytearray
        '''
        delimiterIndex = self._checkDelimiter(pushBuffer)
        del pushBuffer [:delimiterIndex[1]]
        return 

    def _isDataValid(self, pushBuffer, Config) :
        """
        Deprecated \r\n 
        verify if the raw data we received is valid. \r\n 
        search for "xff xff" in ``pushBuffer``. then check if the offset between the first 
        and second "xff xff" equals the number of expected bytes. 

        :param pushBuffer: pushBuffer containing raw data
        :type pushBuffer: bytearray

        :param Config: holds the acquisition configuration information
        :type Config: Licel.licel_acq.Config() 

        :returns: True we received all raw data in ``pushBuffer``, False if some byte were lost 
        :rtype: bool    
        """
        delimiterIndex = self._checkDelimiter(pushBuffer)
        while (((delimiterIndex[1] - delimiterIndex[0])) != Config.exceptedByte and
               ((delimiterIndex[1] != -1  ))) :
                delimiterIndex.pop(1)

        if ((delimiterIndex[1] - delimiterIndex[0]) == Config.exceptedByte):
            return True
        elif (delimiterIndex[1] != -1  ):
            return False 
         
    def parseDataFromBuffer(self, pushBuffer, Config, bigEndianTimeStamp, shots, 
                            TRHardwareInfos):
        '''
        parse the ``pushBuffer``, transfer the binary push data from ``pushBuffer`` into the 
        ``dataSet`` to be later stored in data files. 
        binary push data will be transformed from raw binary data uint8 to preprocessed 
        raw data uint32.
        If the data is valid, meaning no byte were lost during the transmission, we remove
        the raw binary, we successfully preprocessed from ``pushBuffer``

        :param pushBuffer: contain raw binary data .
        :type pushBuffer: bytearray 

        :param Config: holds the acquisition configuration information
        :type Config: Licel.licel_acq.Config()

        :param  bigEndianTimeStamp: indicates if the time stamp endianness. 
        if true time stamp is big endian else time stamp is little endian.
        old Coldfire boards transmit the timestamp as big endian
        
        :type bigEndianTimeStamp: bool 

        :param shots: number of shots the user wishes to acquire
        :type shots: int

        :param TRHardwareInfos: list of dict that contains hardware information for each 
            active transient recorder
        
        :type TRHardwareInfos: dict{Tr_num : dict{'ADC Bits' : ' ', 'PC Bits' : ' ',
                                FIFOLength': ' ', binWidth' : ' ', 'ID' : ' ', 'HWCAP':' ', 
                                'binShift':' ', 'raw': ' '}}

        :returns: 
            - dataValid (bool) - true if we parsed the binary data correctly. \r\n
              false if we did not successfully parsed the binary data for example byte were lost. 
            - DataSet (list [numpy.ndarray(dtype=uint32, ndim =1)] ) - 
              list holding the individual active data sets in the following order: \r\n
              [tr0 analogue mem A, tr0 analogue mem B, tr0 analogue mem C, tr0 analogue mem D,
              tr0 photon mem A, tr0 photon mem B, tr0 photon mem C, tr0 photon mem D, 
              tr1 analogue mem A, tr1 analogue mem B .....]\r\n
              if data set is not active in the configuration they will be omitted in the List 
            - time_stamp (int) - time stamp from the controller in millisec 
            - analogue_shot_dict (dict{'A' : int, 'B': int, 'C': int, 'D': int}) -
              hold the shot number for each analogue dataSet.
              if data set is not active in the configuration shot number will be omitted 
            - pc_shot_dict (dict{'A' : int, 'B': int, 'C': int, 'D': int})- 
              hold the shot number for each photon counting dataSet   
              if data set is not active in the configuration shot number will be omitted  
        '''
        analogue_shot_dict = {}
        pc_shot_dict = {}
        DataSet = []
        parserIndex = 0
        dataValid = False

        if bigEndianTimeStamp == False:
            time_stamp  = int.from_bytes(pushBuffer[2:6], byteorder='little',signed=False)

        elif bigEndianTimeStamp == True:
            time_stamp  = int.from_bytes(pushBuffer[2:6], byteorder='big',signed=False)

        parserIndex += 6 
        for trConfig in Config.TrConfigs: 
            for memory in trConfig.analogueEnabled: 
                if trConfig.analogueEnabled[memory] == True:
                    TRnum = trConfig.nTransientRecorder
                    analogue_shot_dict[memory] =(int.from_bytes([pushBuffer[parserIndex],
                                                                pushBuffer[parserIndex+1]],
                                                        byteorder='little',signed=False))
                    parserIndex += MPUSH_SHOTNUM_OFFSET
                    numberToRead = trConfig.analogueBins[memory] 
                    RawLsw = pushBuffer[parserIndex:(2*numberToRead)+parserIndex]
                    parserIndex += 2*numberToRead 
                    analogue_shot_dict[memory] =(int.from_bytes([pushBuffer[parserIndex],
                                                                pushBuffer[parserIndex+1]],
                                                        byteorder='little',signed=False))
                    parserIndex += MPUSH_SHOTNUM_OFFSET
                    RawMsw = pushBuffer[parserIndex :(numberToRead*2)+ parserIndex]
                    parserIndex += 2*numberToRead 

                    lsw = numpy.frombuffer(RawLsw,numpy.uint16) 
                    msw = numpy.frombuffer(RawMsw,numpy.uint16)  
                    mem_extra = numpy.zeros((numberToRead))
                    if ((shots > 32764) and (TRHardwareInfos[TRnum]['ADC Bits'] == 16)):
                        analogue_shot_dict[memory] =(int.from_bytes(
                                                        [pushBuffer[parserIndex],
                                                        pushBuffer[parserIndex+1]],
                                                        byteorder='little',signed=False))
                        parserIndex += MPUSH_SHOTNUM_OFFSET 
                        rawPHM = pushBuffer[parserIndex :(numberToRead*2)+ parserIndex]
                        parserIndex += 2*numberToRead 
                        mem_extra = numpy.frombuffer(rawPHM,numpy.uint16)  

                    Analogue32BitData,Clip = self.combine_Analog_Datasets_16bit(lsw
                                                                                ,msw,
                                                                                mem_extra)
                    DataSet.append(Analogue32BitData)

            for memory in trConfig.pcEnabled: 
                if trConfig.pcEnabled[memory] == True: 
                    pc_shot_dict[memory] = (int.from_bytes([pushBuffer[parserIndex],pushBuffer[parserIndex+1]],
                                         byteorder='little',signed=False))
                    parserIndex += MPUSH_SHOTNUM_OFFSET

                    numberToRead = trConfig.pcBins[memory]
                    rawPC = pushBuffer[parserIndex:(numberToRead*2)+parserIndex]
                    parserIndex += 2*numberToRead 
                    mem_low  = numpy.frombuffer(rawPC,numpy.uint16)
                    if ((shots > 4096 and TRHardwareInfos[TRnum]['PC Bits'] == 4)
                        or (shots > 1024 and TRHardwareInfos[TRnum]['PC Bits'] == 6)
                        or (shots > 256 and TRHardwareInfos[TRnum]['PC Bits'] == 8)):  
                        pc_shot_dict[memory] = (int.from_bytes([pushBuffer[parserIndex],
                                                            pushBuffer[parserIndex+1]],
                                                            byteorder='little',signed=False))
                        parserIndex += MPUSH_SHOTNUM_OFFSET
                        mem_extra_buffer = pushBuffer[parserIndex:(numberToRead*2)+parserIndex]
                        parserIndex += 2*numberToRead 
                        mem_extra = numpy.frombuffer(mem_extra_buffer,numpy.uint16)
                        convertedPc = self.convert_Photoncounting_Fullword(mem_low, mem_extra)
                        mypc = convertedPc.astype(dtype=numpy.uint32)

                    else : 
                        convertedPc = self.convert_Photoncounting(mem_low, 0)
                        mypc = convertedPc.astype(dtype=numpy.uint32)

                    DataSet.append(mypc)

        if (pushBuffer[parserIndex:parserIndex+2] == b'\xff\xff'): 
            dataValid = True
            del pushBuffer[:parserIndex]

        return dataValid, DataSet, time_stamp, analogue_shot_dict, pc_shot_dict
         
    def _generateFileName(self,prefix):
        """ 
        generate file name from date, as specified in  
        https://licel.com/raw_data_format.html 

        :param prefix: one or two letter prefix as start for the file name
        :type prefix: str

        :returns : constructed file name. 
        :rtype: str
        """
        assert len(prefix) <= 2 , "maximum {prefix: s} length is 2 character\r\n"
        now = datetime.now()
        year = now.year-2000 # 2000 represents the century we are in 
        month = f'{now.month:x}'.upper() # month in Hexadecimal
        day  = now.day
        hour = now.hour
        min = now.minute
        sec = now.second
        millisec = now.microsecond/1000
        filename ='{:s}{:02d}{:s}{:02d}{:02d}.{:02d}{:02d}{:02d}'.format(prefix,
                                                               year, month, day, 
                                                               hour, min,sec,
                                                               int(millisec))
        return filename
    
    def _generateSecondHeaderline(self,Config, startTime,stopTime ):
        """ 
        generate second header line from ``Config``.
        second header line contains info about the system , as specified in  
        https://licel.com/raw_data_format.html 

        :param Config: system configuration 
        :type Config: Licel.licel_acq.Config()

        :param startTime: acquisition start time.
        :type startTime: datetime.datetime.now()

        :param stopTime: acquisition stop time. 
        :type stopTime : datetime.datetime.now()

        :returns: second header line. 
        :rtype: str
        """        
        measInfo = Config.measurmentInfo
        assert len(measInfo.szLocation) <= 8, "Measurement site must be 8 character"
        header =(' {:8s} {:19s} {:19s} {:04d} {:011.6f} {:011.6f} {:04.1f} {:04.1f}\n'
                 .format(measInfo.szLocation,startTime,stopTime,
                         measInfo.nAltitude,measInfo.dLongitude,
                         measInfo.dLatitude,measInfo.Zenith,
                         measInfo.Azimuth))
        return header
    
    def _generateThirdHeaderline(self,Config, shots, timestamp):
        """
        generate third header from  ``Config``, as specified in  
            https://licel.com/raw_data_format.html
        
        :param Config: system configuration 
        :type Config: Licel.licel_acq.Config()
        
        :param iShots: number of shots. 
        :type iShots: uint 

        :param timestamp: timestamp received with from the controller in millisec
        :type timestamp: uint 
        """
        measurConf = Config.measurmentInfo
        myDataSetsnum = 1
        header =(' {:d} {:04d} {:07d} {:04d} {:02d} {:07d} {:04d} {:d}\n'
                 .format(shots, measurConf.repRateL0, shots, 
                         measurConf.repRateL1, Config.numDataSets,
                         shots, measurConf.repRateL2, timestamp) ) 
        return header

    def _generateDatasetsHeaderline(self, Config, TRHardwareInfo, 
                                    analogue_shot_dict, pc_shot_dict):
        """
        generate header lines specific to the data sets,for each 
        active data set in ``Config``, as specified in  
        https://licel.com/raw_data_format.html

        :param Config: holds the acquisition configuration information
        :type Config: Licel.licel_acq.Config() 

        :param TRHardwareInfos: dictionary holding TRHardwareinfo for each detected 
            transient recorder. 
        
        :type TRHardwareInfos: dict{Tr_number : {TRHardwareInfo}}

        :param analogue_shot_dict: contains information about shot number for each active 
            analogue memory
        :type analogue_shot_dict: dict{'A' : int, 'B' : int, 'C': int, 'D' : int }

        :param analogue_shot_dict: contains information about shot number for each active 
            photon counting memory
        :type analogue_shot_dict: dict{'A' : int, 'B' : int, 'C': int, 'D' : int }
        """
        myHeaderLine = ""
        for trConfig in Config.TrConfigs: 
            for key in trConfig.analogueEnabled: 
                if trConfig.analogueEnabled[key] == True: 
                    trNum = trConfig.nTransientRecorder
                    binshift_decimal = int((TRHardwareInfo[trNum]['binShift'] % 1) * 1000)

                    pol = self._convertPolarizationToFileNotation(trConfig.analoguePolarisation[key])
                    header =(" 1 0 {laser} {dataPoints} {laserPolarization} {pmtHV:04d}"
                             " {binwidth:1.2f} {wavelength:05d}.{polStatus} 0 0"
                             " {binshift:02d} {binshift_dec:3d} {adc:02d}"
                             " {shots:06d} 0.{myRange:03d} BT{trNum:1X}\n"
                            .format(laser = trConfig.laserAssignment[key], 
                                   dataPoints = (trConfig.analogueBins[key]-1),
                                   laserPolarization = trConfig.analoguePolarisation[key],
                                   pmtHV = int(trConfig.pmVoltageAnalogue[key]),
                                   binwidth = float(TRHardwareInfo[trNum]['binWidth']),
                                   wavelength = int (trConfig.analogueWavelength[key]),
                                   polStatus = pol,
                                   binshift = int(TRHardwareInfo[trNum]['binShift']), 
                                   binshift_dec = int (binshift_decimal), 
                                   adc = TRHardwareInfo[trNum]['ADC Bits'], 
                                   shots = analogue_shot_dict[key], 
                                   myRange = trConfig.nRange,
                                   trNum = trConfig.nTransientRecorder)   )
                    myHeaderLine += header
            
            for key in trConfig.pcEnabled: 
                if trConfig.pcEnabled[key] == True: 
                    binshift_decimal = int ((TRHardwareInfo[trNum]['binShift'] % 1) * 1000)
                    pol = self._convertPolarizationToFileNotation(trConfig.pcPolarisation[key])
                    scalingFactor = 25/63  # from labview 
                    header =(" 1 1 {laser} {dataPoints} {laserPolarization} {pmtHV:04d}"
                             " {binwidth:1.2f} {wavelength:05d}.{polStatus} 0 0 00 000 00"
                             " {shots:06d} {myRange:6.4f} BC{trNum:1X}\n"
                            .format(laser = trConfig.laserAssignment[key], 
                                   dataPoints = (trConfig.pcBins[key]-1),
                                   laserPolarization = trConfig.pcPolarisation[key],
                                   pmtHV = int(trConfig.pmVoltagePC[key]),
                                   binwidth = float(TRHardwareInfo[trNum]['binWidth']),
                                   wavelength = int (trConfig.pcWavelength[key]),
                                   polStatus = pol,
                                   binshift = int("00"), 
                                   binshift_dec = int ("000"), 
                                   adc = TRHardwareInfo[trNum]['ADC Bits'], 
                                   shots = pc_shot_dict[key], 
                                   myRange = (trConfig.discriminator * scalingFactor),
                                   trNum = trConfig.nTransientRecorder))
                    myHeaderLine += header   

        return myHeaderLine

    def _convertPolarizationToFileNotation(self, polarization):
        """ 
        convert ``polarization`` from Config (int) to polarization file notation(str)

        :param polarization: polarization (0, 1, 2, 3, 4) correspand to o|p|s|r|l
        :type polarization: int 

        :returns: polarization status (none, parallel, crossed, right circular, left circular) o|p|s|r|l
        :rtype: str
        """
        if polarization == 0 : 
            return "o"
        if polarization == 1 : 
            return "p"
        if polarization == 2 : 
            return "s"
        if polarization == 3 : 
            return "r"
        if polarization == 4 : 
            return "l"
        
    def saveFile(self, DataSet, Config,  startTime, stoptTime,
                 TRHardwareInfo, time_stamp, analogue_shot_dict,
                 pc_shot_dict, shots, ACQUISPERFILE ):
        '''
        Save the acquired DataSet to the file path specified in the configuration in the 
        Licel file format. for more information about licel file format see:
        https://licel.com/raw_data_format.html

        :param DataSet: holds the acquired dataset 
        :type DataSet: list[numpy.ndarray(dtype=uint32, ndim =1)] 

        :param Config: holds the acquisition configuration information
        :type Config: Licel.licel_acq.Config()

        :param startTime: acquisition start time.
        :type startTime: datetime.datetime.now()

        :param stopTime: acquisition stop time. 
        :type stopTime: datetime.datetime.now()

        :param time_stamp: time stamp from the controller in millisec 
        
        :param analogue_shot_dict: hold the shot number for each analogue dataSet.
            if data set is not active in the configuration shot number will be omitted 
        :type analogue_shot_dict: (dict{'A' : int, 'B': int, 'C': int, 'D': int}) -
        
        :param pc_shot_dict: hold the shot number for each photon counting dataSet   
            if data set is not active in the configuration shot number will be omitted 
        :type pc_shot_dict: (dict{'A' : int, 'B': int, 'C': int, 'D': int})- 
        '''    
        # file name needs to be written for each acquisition,
        # it holds the timestamp of the acquisition
        filename = self._generateFileName(Config.measurmentInfo.cFirstLetter)
        
        if (self._acquisWrittenToFile > ACQUISPERFILE -1 or 
            self._acquisWrittenToFile == 0) :

            self._acquisWrittenToFile = 0
            self._path = os.path.join(Config.measurmentInfo.szOutPath,filename)
        
        my_startTime = startTime.strftime("%d/%m/%Y %H:%M:%S")
        my_stoptTime = stoptTime.strftime("%d/%m/%Y %H:%M:%S")

        f = open(self._path, "a")
        f.write(" {filename}\n".format(filename=filename))
        f.write(self._generateSecondHeaderline(Config,my_startTime, my_stoptTime))
        f.write(self._generateThirdHeaderline(Config, int(shots), int(time_stamp)))
        f.write(self._generateDatasetsHeaderline(Config, TRHardwareInfo, 
                                                 analogue_shot_dict, pc_shot_dict))
        f.write('\n')
        f.close()

        f = open(self._path, "ab")        
        for Set in DataSet:
            f.write(Set)
            f.write(b'\r\n')

        f.close()
        self._acquisWrittenToFile += 1

    def pushDataLog(self, asciiFile_path, pushBuffer, idn, timestamp, Config):
        """
        write log file to spcified ``asciiFile_path``

        :param asciiFile_path: path of the file to be written 
        :type asciiFile_path: str

        :param pushBuffer: pushBuffer 
        :type pushBuffer: bytearray 

        :param idn: controller identification string 
        :type idn: str 

        :param timestamp: controller timestamp in millisec 
        :type timestamp: int

        :param Config: holds the acquisition configuration information
        :type Config: Licel.licel_acq.Config()
        """
        #binaryFile = open(binaryFile_path, "ab")
        delimiter = self._checkDelimiter(pushBuffer)
        asciiFile  = open(asciiFile_path, "a")
        bufferlength = "raw buffer length:" + str(len(pushBuffer)) + "\r\n"
        byte_to_recive = "bin to recive:" + str(Config.BufferSize) + "\r\n"
        delimiterPos = "delimiter : "+ str(delimiter) + "\r\n"
        timestamp = str(timestamp)+ "\r\n"
        asciiFile.write(idn+ "\r\n")
        asciiFile.write(str(Config.TrConfigs)+ "\r\n")
        asciiFile.write(bufferlength)
        asciiFile.write(byte_to_recive)
        asciiFile.write(delimiterPos)
        asciiFile.write(str(pushBuffer))
        asciiFile.write(timestamp)
        asciiFile.write("\r\n")
        asciiFile.close()

