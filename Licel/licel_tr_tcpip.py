from Licel import TCP_util
from types import MappingProxyType
import time
import numpy



# Datasets
DATASETSTYPE =MappingProxyType( { 
'PC'  : 'PC'  ,
'PHM' : 'PHM' ,
'LSW' : 'LSW' ,
'MSW' : 'MSW' ,
'PHM' : 'PHM' ,
'P2L' : 'P2L' ,
'P2M' : 'P2M' ,
'A2L' : 'A2L' ,
'A2M' : 'A2M' ,
'A2H' : 'A2H'    
})

# Memory 
MEMORY = MappingProxyType({
'MEM_A' : 'A',
'MEM_B' : 'B',
'MEM_C' : 'C',
'MEM_D' : 'D'
})

#PUSH MODE TYPE
PUSHMODETYPE = MappingProxyType({
'PHO' : 'PHO',
'LSW' : 'LSW',
'MSW' : 'MSW' 
})

#input range
INPUTRANGE = MappingProxyType({ '-500mV': 0, '-100mV': 1, '-20mV' : 2 })

# TRTYPE holds hardware info
# default TRHardwareinfo will be returned for transient produced before 2009 


TRHardwareInfo_default = { 'ADC Bits' : 12, 'PC Bits' : 4, 'FIFOLength': 16384,
                           'binWidth' : 7.5,'ID' :0, 'HWCAP' : 0, 'binShift': 3.0,
                           'raw':0}

#Threshold Modes 
THRESHOLD_LOW = 0
THRESHOLD_HIGH = 1

MAX_SQUARE_SIZE = 4000

# HWCAP Fields 
SHOTCOUNTER_B        = 0x01
SHOTCOUNTER_C        = 0x02
SHOTCOUNTER_D        = 0x04
PRETRIGGER           = 0x08
BLOCK_GLOBAL_TRIGGER = 0x10
SQUARED_DATA         = 0x20
FREQ_DIVIDER         = 0x40

class TransientRecorder(TCP_util.util):

    Tr_number = " "

    def __init__(self, commandSocket, pushSocket, killSocket, socket_File ) -> None:
#        self.Tr_number = TR_num
        self.state = { "memory" : MEMORY['MEM_A'] ,
                       "recording": False , "acquisitionState": False}
        self.commandSocket  = commandSocket
        self.PushSocket     = pushSocket 
        self.sockFile       = socket_File
        self.killsock       = killSocket
    
    def getStatus(self) -> list [bool,bool,str,int]:
        ''' Return the shot number for each memory, there is one clearing cycle at the start.'''
        acquisitionState =False
        recording = False
        memory = "MEM_A "
        resp = self._writeReadAndVerify("STAT?", "Shots")
        if resp.find("Armed") != -1:
            acquisitionState = True    
            recording = True
        if resp.find("MemB") != -1:
            memory = "MEM_B"
        shots = resp.split(" ")[1]
        return acquisitionState, recording, memory,int(shots)
    
    def setSlaveMode(self) -> str: 
        ''' 
        Set slave mode. End push mode 
        for more information: https://licel.com/manuals/ethernet_pmt_tr.pdf#TCPIP.SLAVE
        '''
        return self._writeReadAndVerify("SLAVE", "executed")
    
    def clearMemory(self) -> str: 
        ''' 
        Clear both memories (A and B) of the previously selected device.
        For more info visit: https://licel.com/manuals/ethernet_pmt_tr.pdf#TCPIP.CLEAR
        '''
        return  self._writeReadAndVerify("CLEAR", "executed")
    
    def multipleClearMemory(self) -> str:
        ''' Clear both memories (A and B) of the previously selected devices.'''
        return  self._writeReadAndVerify("MCLEAR", "executed")
    
    def enablePretrigger(self) -> str:
        '''
        Enable the pretrigger for a selected TR. In TR20-16bit this will be 128 bins 
        long shipped till 2018, since 2018 the TR40-16bit-3U will have 1/16 of the 
        trace length. This means for a 16k the pretrigger will be 1024 bins long. 
        The TR will power up with pretrigger off.  
        TR devices supporting pretrigger indicate it by bit 3 in the HWCAP field of 
        the TRTYPE? command.
        '''
        return  self._writeReadAndVerify("PRETRIG 1", "executed")
    
    def disablePretrigger(self) -> str:
        ''' Disable the pretrigger for a selected TR'''
        return  self._writeReadAndVerify("PRETRIG 0", "executed")
    
    def startAcquisition(self) -> str :
        ''' Start the currently selected transient recorder.'''
        return  self._writeReadAndVerify("START", "executed")
    
    def stopAcquisition(self) -> str: 
        ''' Stops the currently selected transient recorder.'''
        self.writeCommand("STOP")
        resp = self.readResponse()
        assert resp.find("STOP executed") >=0, "\r\nLicel_TCPIP_StopAcquisition - Error 5094: " + resp
        return  self._writeReadAndVerify("STOP", "executed")
    
    def setShotLimit(self, limit : str) -> str:
        '''
        Switch between 4k and 64k maxshots. 
        permissable arguments are : \r\n
        limit = str "64K" \r\n
        limit = str "4K"  \r\n
        '''
        if (not ((limit != '64K') ^ (limit != '4K'))):
            raise ValueError ('setShotLimit argument can only be "64K", "4K" ')
        cmd = "LIMIT " + limit 
        return  self._writeReadAndVerify(cmd, "executed")
    
    def setMaxBins(self, numMaxBins : int) -> str:
        '''
        Sets the tracelength if the memory configuraton switch 5 is in the ON Position.
        A user defined tracelength allows a better usage of 
        the acquisition time for high repetition rate systems.
        '''
        #Check validity of maxbins ??
        if (not ((numMaxBins >= 2) and (numMaxBins <= 32768))):
            raise ValueError ('setMaxBins Valid range is between 2 to 32768')
        cmd = "SETMAXBINS "+ str(numMaxBins)
        return  self._writeReadAndVerify(cmd, "executed")
    
    def setMaxShots(self, maxShots : int) ->str:
        '''
        Set the maxmimum  shotnumber of the TR this can be an arbitrary number 
        between 2 and 65335, the startup default is 4096. This will work with newer 
        TR. If this command fails and the unit claims that it supports 64k shots then
        Licel_TCPIP_SetShotLimit will work.
        '''        
        if (not (maxShots <= 65534 and maxShots >= 1)):
            raise ValueError ('setMaxShots argument must be in range of (1 ... 65534) ')
        cmd = "SETMAXSHOTS "+ str(maxShots)
        return  self._writeReadAndVerify(cmd, "executed")
 
    def singleShot(self) -> str:
        '''
        Start the currently selected transient recorder.
        '''
        return  self._writeReadAndVerify("SINGLE", "executed")

    def setThresholdMode(self, thresholdMode : str) -> str:
        '''
        Sets the damping state to either on or off.
        If a value of 1 is sent then damping is turned on. If a value
        of 0 is sent, the damping is turned off. 
        When the damping is set to low, a discriminator level of 63 outputs -25mV
        When the damping is set to High, a discriminator level of 63 outputs -100mV
        '''
        if (not ((thresholdMode != 'ON') ^ (thresholdMode != 'OFF'))):
            raise ValueError ('setThresholdMode argument must be either "ON" or "OFF" \r\n passed argument is :'+thresholdMode)
        if (thresholdMode == 'ON'):
            cmd = "THRESHOLD 1"
        if (thresholdMode == 'OFF'):
            cmd = "THRESHOLD 0"
        return  self._writeReadAndVerify(cmd, "Damping")
    
    def setInputRange(self, Range : str ) -> str:
        '''
        Change the input voltage range. \r\n
        permissable parameters are:     \r\n
        * "-500mV"                     
        * "-100mV" 
        * "-20mV"          
        '''
        if (not (Range in INPUTRANGE.keys())):
            raise ValueError ('setInputRange argument must be either "-500mV", "-100mV", "-20mV" \r\n passed argument is :'+ Range)
        cmd = (("RANGE "+str(INPUTRANGE[Range])))
        verify = "set to " + Range
        return  self._writeReadAndVerify(cmd, verify)

    def _getFreqDivider(self) -> str:
        '''
        Retrieve the frequency divider, the values are valid only for units 
        supporting this feature, to get the actual binwidth multiply the binwidth 
        returned by TRTYPE with the (1 <<freqDividerExponent).\r\n
        The binwidth reported by 
        TRType needs then to be multiplied with (1 <<freqDividerExponent)
        '''
        return  self._writeReadAndVerify("FREQDIV?", " ")
    
    def _setFreqDivider(self, freqDivider : int) -> str:
        '''
        Set the frequency divider, this will have effect only on units  
        supporting this feature, it changes the sampling rate before the summation 
        of the data.
        '''
        exponent = 0
        if (freqDivider > 128 or freqDivider < 0):
            raise ValueError ('freqDivider exponent must be in Range of 0 ... 128 \r\n passed argument is :'+ str(freqDivider))
        while(freqDivider > 1):
            freqDivider = freqDivider /2
            exponent +=1
        cmd ="FREQDIV "+ str(exponent)+" 0"
        return self._writeReadAndVerify(cmd, str(exponent))
    
    def _isPowerofTwo(self, number : int):
        '''
        helper function to check if number is power of two or zero. 
        return true if number is power of 2 or zero.
        '''
        return (number & (number-1) == 0)
    
    def TRtype(self) -> dict:
        '''
        Get transient recorder hardware information for the selected transient 
        recorder. Old TR produced before Oct. 2009 will not support this command 
        If this command is not supported default values  for a TR20-160 are filled in

        :returns: dictionary containing  hardware info
        :rtype:  dict{'ADC Bits' : ' ', 'PC Bits' : ' ' , 'FIFOLength': ' ' ,
            binWidth' : ' ','ID' : ' ', 'HWCAP' : ' ', 'binShift': ' ', 'raw': ' '}
        '''
        tempTRHardwareInfo = {}
        resp = self._writeReadAndVerify("TRTYPE?", "TRTYPE ADC Bits")        
        parsedResp = resp.split(" ")
        tempTRHardwareInfo["ADC Bits"] = int(parsedResp[3])
        tempTRHardwareInfo["PC Bits"] = int(parsedResp[6])
        tempTRHardwareInfo["FIFOLength"]= int(parsedResp[8])
        tempTRHardwareInfo["binWidth"] = float(parsedResp[10])
        tempTRHardwareInfo["ID"] = parsedResp[12]
        tempTRHardwareInfo["HWCAP"] = parsedResp[14]
        tempTRHardwareInfo["binShift"] = float(parsedResp[16])
        #self.TRHardwareInfo["raw"]= parsedResp[18]
        return tempTRHardwareInfo
       
    def continueAcquisition(self) -> str: 
        '''
        Continue the recording process for the previously specified device without 
        reinitializing the memory.
        '''
        self.writeCommand("CONTINUE")
        resp = self.readResponse()
        assert resp.find("CONTINUE executed") >=0, "\r\nLicel_TCPIP_ContinueAcquisition - Error 5093 : " + resp
        return self._writeReadAndVerify("CONTINUE", "executed")

    def _readData(self, numberToRead : int) -> bytearray :
        '''
        Wait until the the number of scans defined by Number to Read is available
        and reads them or returns a timeout error if the timeout ms is exceeded.
        Read binary data into a byte array. Transient recorder data is internally
        16bits wide so for every data point two bytes need to be fetched
        '''
        return self.recvall(numberToRead)

    def _requestData(self, device : int, numberToRead : int,
                    datatype : str, memory : str ) -> str :
        '''
        Requesting the raw data sets ( analog LSW, analog MSW or photon counting) from
        the specified device for later read.
        '''
        if (not (datatype in DATASETSTYPE.keys())):
            raise ValueError ('_requestDataSet datatype can be :'+ str(DATASETSTYPE.keys())+'\r\n passed argument is :'+ datatype)
        if (not (memory in MEMORY.keys())):
            raise ValueError ('_requestDataSet memory can be :'+ str(MEMORY.keys())+'\r\n passed argument is :'+ memory)
        commadTosend = "DATA? " + str(device) + " " + str(numberToRead) +" "+ DATASETSTYPE[datatype] +" "+ MEMORY[memory]
        self.writeCommand(commadTosend)

    def _getDataSet(self, device : int, numberToRead : int,
                    datatype : str, memory : str ) -> bytearray :
        '''
        Reading the raw data sets ( analog LSW, analog MSW or photon counting) from
        the specified device.
        '''
        self._requestData(device, numberToRead, datatype, memory)
        data = self._readData(numberToRead)
        return data
    
    def getShotsAB(self) -> str:
        '''
        Return the shot number for each memory, there is one clearing cycle at the start.
        '''
        return self._writeReadAndVerify("SHOTAB?", "SHOTAB")
    
    def getMultipleShotsAB(self) -> str: 
        '''
         Return the shotnumber for each memory, there is one clearing cycle at the start.
        '''
        return self._writeReadAndVerify("MSHOTAB?", "MSHOTAB")

    def getMultipleShots(self) -> str: 
        '''
        Return the shotnumber for each memory, there is one clearing cycle at the start.
        '''
        return self._writeReadAndVerify("MSHOTS?", "MSHOTS")

    def multipleClearMemory(self) -> str:
        '''
        Clears both memories (A and B) of the currently selected devices.
        '''
        return self._writeReadAndVerify("MCLEAR", "executed")

    def multipleContinueAcquisition(self) -> str:
        '''
        The acquisition process of the selected multiple devices will be restarted
        without clearing their memories.
        '''
        return self._writeReadAndVerify("MCONTINUE", "executed")

    
    def multipleStartAcquisition(self) -> str:
        '''
        The acquisition process will be started with the next received trigger for
        multiple devices
        '''
        return self._writeReadAndVerify("MSTART", "executed")

    
    def multipleStopAcquisition(self) -> str: 
        '''
        The acquisition process will be stoped after the next received trigger for
        multiple devices
        '''
        return self._writeReadAndVerify("MSTOP", "executed")   
    
    def multipleWaitForReady(self, milliSec: int) -> str: 
        '''
        Wait `milliSec` until all devices returned from the armed state.

        
        :param milliSec: milliseconds to wait, maximum is 400ms 
        :type milliSec: int

        :returns: controller response containing `executed` if successful else failed. 
        :rtype: string
        '''
        command = "MWAIT " + str(milliSec) 
        return self._writeReadAndVerify(command, "executed")

    
    def selectMultipleTR(self, devicelist: list[int]) -> str:
        '''
        The TR corresponding to the numbers in the device list will be
        selected which means that they will become sensitive to all future commands
        that do not require a device number input. The devices will be deselected
        if another select command is issued.
        '''
        command = "SELECT "
        for item in devicelist:
            command += (str(item) + ",")
        command = command[:len(command)-1]
        return self._writeReadAndVerify(command, "executed")

    
    def setDiscriminatorLevel(self, discriminatorLevel:int ) -> str:
        '''
        Set the discriminator level between 0 and 63 for the selected transient
        recorders.
        When the threshold mode is activated, a discriminator level of 63 outputs -100mV
        When the threshold mode is deactivated, a discriminator level of 63 outputs -25mV
        '''
        if (discriminatorLevel <0 or discriminatorLevel > 63): 
            raise ValueError ('setDiscriminatorLevel() discriminatorLevel must be in range 1 ... 63 \r\n passed argument is :'+ str(discriminatorLevel))
        command = "DISC " + str(discriminatorLevel)
        return self._writeReadAndVerify(command, "set to")

       
    def waitForReady(self,delay: int) -> str:
        """
        Waits for return of the device from the armed state. If the waiting time
        is longer than the time specified by delay than the device remains armed
        and will be return to the idle state with next reading of binary data
        a stop command should have been sent before to the transient recorder.
        :param delay: delay in ms
        :type delay: int 

        :returns: if timeout occurs ``timeout`` else ''Device returned from armed state''
        :rtype: str
        """
        acquisitionState =False
        recording = False
        memory = " "
        start = (time.time()*1000)
        while (time.time()*1000) < start + delay:
            acquisitionState, recording, memory,shots =self.getStatus()
            if not acquisitionState :
                return "Device returned from armed state \r\n"
        raise RuntimeError ("Transient recorder did not return from armed state\r\n")
    

    def getCombinedRawAnalogueData(self, TRType, dataParser, bins, shots, device, memory):
        """
        get the combined raw analogue data set. 

        :param TRType: dict holding information about the transient recorder hardware
        :type TRType: dict{'ADC Bits' :" " , 'PC Bits' : " ", 'FIFOLength': " ",
                           'binWidth' :" " , 'ID' : " ", 'HWCAP' : " ", 'binShift': " "}

        :param dataParser: Class holding method for processing and parsing raw data
        :type dataParser: Licel.licel_data.DataParser

        :param bins: number of bins to read. 
        :type bins: int 

        :param shots: number of acquired shots. 
        :type shots: int 

        :param device: transient recorder address 
        :type device: int 

        :param memory: memory to read. 
        :type memory: str can be: 'MEM_A', 'MEM_B', 'MEM_C', 'MEM_D' 

        :returns: combined analogue data set and the clipping information for each data point. 
        :rtype: [Analogue data set: numpy.ndarray(dtype=uint32, ndim =1), 
                 Clipping information: numpy.ndarray(dtype=uint32, ndim =1)]
        """
        if TRType['ADC Bits'] == 16 :
            mem_low_buffer  = self._getDataSet(device, bins + 1, "LSW", memory)   
            mem_high_buffer = self._getDataSet(device, bins + 1, "MSW", memory)
            mem_low   = numpy.frombuffer(mem_low_buffer,numpy.uint16)
            mem_high  = numpy.frombuffer(mem_high_buffer,numpy.uint16)
            mem_extra = numpy.zeros((bins))
            if shots > 4096 :
                mem_extra_buffer = self._getDataSet(device, bins + 1,"PHM", memory)
                mem_extra = numpy.frombuffer(mem_extra_buffer,numpy.uint16)
            return  dataParser._combine_Analog_Datasets_16bit(mem_low, mem_high, mem_extra)
        else : 
            mem_low_buffer  = self._getDataSet(device, bins + 1, "LSW", memory)   
            mem_high_buffer = self._getDataSet(device, bins + 1, "MSW", memory)
            mem_low  = numpy.frombuffer(mem_low_buffer,numpy.uint16)
            mem_high = numpy.frombuffer(mem_high_buffer,numpy.uint16)
            return dataParser._combine_Analog_Datasets(mem_low, mem_high)

    def getCombinedRawAnalogueSquaredData(self, dataParser, binsSqd, device, memory): 
        """
        get the combined raw analogue squared data 

        :param dataParser: Class holding method for processing and parsing raw data
        :type dataParser: Licel.licel_data.DataParser

        :param binsSqd: number of bins to read. 
        :type bins: int 

        :param device: transient recorder address 
        :type device: int 

        :param memory: memory to read. 
        :type memory: str can be: 'MEM_A', 'MEM_B', 'MEM_C', 'MEM_D' 

        :returns: the combined raw analogue squared data
        :rtype: numpy.ndarray(dtype=uint64, ndim =1)
        """
        mem_low_buffer   = self._getDataSet(device, binsSqd + 1, "A2L", memory) 
        mem_high_buffer  = self._getDataSet(device, binsSqd + 1, "A2M", memory)
        mem_extra_buffer = self._getDataSet(device, binsSqd + 1, "A2H", memory) 
        mem_low   = numpy.frombuffer(mem_low_buffer, numpy.uint16)
        mem_high  = numpy.frombuffer(mem_high_buffer, numpy.uint16)
        mem_extra = numpy.frombuffer(mem_extra_buffer, numpy.uint16)

        return dataParser._combineAnalogSquaredData(mem_low, mem_high, mem_extra)

    def getRawPhotonCountingData(self, TRType, dataParser, bins, shots, device, memory):

        """
        get the raw photon data set. 

        :param TRType: dict holding information about the transient recorder hardware
        :type TRType: dict{'ADC Bits' :" " , 'PC Bits' : " ", 'FIFOLength': " ",
                           'binWidth' :" " , 'ID' : " ", 'HWCAP' : " ", 'binShift': " "}

        :param dataParser: Class holding method for processing and parsing raw data
        :type dataParser: Licel.licel_data.DataParser

        :param bins: number of bins to read. 
        :type bins: int 

        :param shots: number of acquired shots. 
        :type shots: int 

        :param device: transient recorder address 
        :type device: int 

        :param memory: memory to read. 
        :type memory: str can be: 'MEM_A', 'MEM_B', 'MEM_C', 'MEM_D' 

        :returns: photon data set. 
        :rtype: numpy.ndarray(dtype=uint32, ndim =1)
        """      
        if((TRType['PC Bits'] == 4  and shots > 4096) or 
        (TRType['PC Bits'] == 6 and shots > 1024) or 
        (TRType['PC Bits'] == 8 and shots > 256)) :
            mem_low_buffer   = self._getDataSet(device, bins + 1, "PC" , memory) 
            mem_extra_buffer = self._getDataSet(device, bins + 1 , "PHM",memory) 
            mem_low   = numpy.frombuffer(mem_low_buffer,numpy.uint16)
            mem_extra = numpy.frombuffer(mem_extra_buffer,numpy.uint16)
            return dataParser._convert_Photoncounting_Fullword(mem_low, mem_extra)

        else: 
            PUREPHOTON = 0
            mem_low_buffer   = self._getDataSet(device, bins + 1, "PC" , memory) 
            mem_low   = numpy.frombuffer(mem_low_buffer,numpy.uint16)
            return dataParser._convert_Photoncounting(mem_low, PUREPHOTON)

    def getRawPhotonCountingSquaredData(self, dataParser, binsSqd, device, memory):
        """
        get the photon counting raw  squared data 

        :param dataParser: Class holding method for processing and parsing raw data
        :type dataParser: Licel.licel_data.DataParser

        :param binsSqd: number of bins to read. 
        :type bins: int 

        :param device: transient recorder address 
        :type device: int 

        :param memory: memory to read. 
        :type memory: str can be: 'MEM_A', 'MEM_B', 'MEM_C', 'MEM_D' 

        :returns: the combined  photon counting raw squared data
        :rtype: numpy.ndarray(dtype=uint64, ndim =1)
        """
        mem_low_buffer   = self._getDataSet(device, binsSqd + 1, "P2L", memory) 
        mem_high_buffer  = self._getDataSet(device, binsSqd + 1, "P2M", memory)
        mem_low   = numpy.frombuffer(mem_low_buffer,numpy.uint16)
        mem_high  = numpy.frombuffer(mem_high_buffer,numpy.uint16)

        return dataParser._combine_Photon_Squared_Data(mem_low, mem_high)

    



