from Licel import TCP_util, licel_tcpip
from types import MappingProxyType
import time
import numpy
import select

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from typing import TextIO 
    from Licel import licel_data, licel_Config

# Block rack trigger accepted string 
BLOCKTRIGGER = {"BLOCK A", "BLOCK B", "BLOCK C", "BLOCK D"}
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


TRHardwareInfo_default: dict[str, int | float] = { 
                           'ADC Bits' : 12, 'PC Bits' : 4, 'FIFOLength': 16384,
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

HEADEROFFSET = 3 # 3* 2 byte = 6byte represents first delimiter xff xff + timestamp 
NEXT_DELIMTER_OFFSET = 2 # 2 byte representing the next delimiter xff xff
class TransientRecorder(TCP_util.util):

    Tr_number = " "
    __MaxTrNumber = 0
    __TrDict: dict[str, str] = {}

    bigEndianTimeStamp = False

    pushBuffer = bytearray()

    #: holds the total number of raw datasets to be read, MSW LSW PC PHM   
    __rawDataSets__ : int = 0  
    #: holds the total number of bins to be read.
    totalnumBins : int = 0 
    #: Buffer size to receive MPUSH data
    BufferSize : int = 0 
    #: number of byte expected to be received for a complete data set      
    exceptedByte : int = 0  

    #: a dictionary  containing hardware info for each active transient recorder.
    #  dict{Tr_num : dict{'ADC Bits' : ' ', 'PC Bits' : ' ' , 'FIFOLength': ' ' ,
    #                     'binWidth' : ' ', 'ID' : ' ', 
    #                     'HWCAP' : ' ', 'binShift': ' ', 'raw': ' '}}
    hardwareInfos:dict[int, dict[str, int | str | float]] = {}

    def __init__(self,
                 commandSocket: TCP_util.socket.socket,
                 pushSocket: TCP_util.socket.socket,
                 killSocket: TCP_util.socket.socket,
                 socket_File ) -> None:
#        self.Tr_number = TR_num
        self.state: dict[str, bool | str] = { "memory" : MEMORY['MEM_A'] ,
                       "recording": False , "acquisitionState": False}
        self.commandSocket  = commandSocket
        self.PushSocket     = pushSocket 
        self.sockFile       = socket_File
        self.killsock       = killSocket
    
    def getStatus(self) -> tuple[bool, bool, str,int]:
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
    
    def blockRackTrigger(self, trig: str) -> str:
        '''
        Block a trigger related to the acquisition at the specified Memory = A, B, C, or D. The typical use case
        is when the rack trigger A and B are driven but a certain channel should be active only when trigger
        A or B arrives
        To unblock Trigger see ``unblockRackTrigger``

        :param trig: trigger to be blocked, possible value are ``A``, ``B``, ``C``, ``D``
        :type trig: str

        '''
        mode ="BLOCK " + trig
        if (not (mode in BLOCKTRIGGER )) :
            raise ValueError ('Argument can only be "A", "B", "C", "D"')
        self.writeCommand(mode)
        resp = self.readResponse()
        assert resp == "BLOCK executed\n", "\r\nLicel_TCPIP_BlockRackTrigger - Error 5108 : " + resp
        return resp
    
    def unblockRackTrigger(self) -> str:
        '''
        To unblock previously blocked triggers by ``blockRackTrigger``
        '''
        self.writeCommand("BLOCK OFF")
        resp = self.readResponse()
        assert resp == "BLOCK executed\n", "\r\nLicel_TCPIP_UnblockRackTrigger - Error 5108 : " + resp
        return resp
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
        cmd = " "
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
    
    def TRtype(self) -> dict[str, int | float | str]:
        '''
        Get transient recorder hardware information for the selected transient 
        recorder. Old TR produced before Oct. 2009 will not support this command 
        If this command is not supported default values  for a TR20-160 are filled in

        :returns: dictionary containing  hardware info
        :rtype:  dict{'ADC Bits' : ' ', 'PC Bits' : ' ' , 'FIFOLength': ' ' ,
            binWidth' : ' ','ID' : ' ', 'HWCAP' : ' ', 'binShift': ' ', 'raw': ' '}
        '''
        tempTRHardwareInfo : dict[str, int | float | str] = {}
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

    def _readData(self, numberToRead : int) -> bytearray | None :
        '''
        Wait until the the number of scans defined by Number to Read is available
        and reads them or returns a timeout error if the timeout ms is exceeded.
        Read binary data into a byte array. Transient recorder data is internally
        16bits wide so for every data point two bytes need to be fetched
        '''
        return self.recvall(numberToRead)

    def _requestData(self, device : int, numberToRead : int,
                    datatype : str, memory : str ) -> None :
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
                    datatype : str, memory : str ) -> bytearray | None :
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
    

    def getCombinedRawAnalogueData(self, TRType: dict[str, int | float | str],
                                   dataParser: 'licel_data.DataParser',
                                   bins: int, shots: int, device: int,
                                   memory: str) ->tuple[numpy.ndarray[Any, numpy.dtype[numpy.uint32]],
                                                        numpy.ndarray[Any, numpy.dtype[numpy.uint32]]]:
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

    def getCombinedRawAnalogueSquaredData(self, dataParser:'licel_data.DataParser',
                                          binsSqd: int, device: int, memory: str) -> numpy.ndarray[Any, numpy.dtype[numpy.uint64]]: 
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

    def getRawPhotonCountingData(self, TRType:dict[str, int | str |float],
                                 dataParser:'licel_data.DataParser', bins: int, 
                                 shots: int, device: int, 
                                 memory: str) -> numpy.ndarray[Any, numpy.dtype[numpy.uint32]]:

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

    def getRawPhotonCountingSquaredData(self, dataParser:'licel_data.DataParser',
                                        binsSqd: int, device: int,
                                        memory: str) -> numpy.ndarray[Any, numpy.dtype[numpy.uint64]]:
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
    
    def MPushStop(self) -> str: 
        """ 
        stops the push/mpush mode. Internally it sends a ``SLAVE`` command.
        for more information: https://licel.com/manuals/ethernet_pmt_tr.pdf#TCPIP.SLAVE
        :raises Exception: if the stop command is not executed.

        :returns: Controller response.
        :rtype: str 
        """
        return self.setSlaveMode()


    def selectTR(self, numTR : int) -> str: 
        """
        select transient recorder to communicate with. 

        :param numTR: transient recorder adresse between 0 .. 15
        :type numTR: int 

        :returns: ``select numTR executed`` or 
            ``Device ID ``numTR` is currently not supported``

        :rtype: str
        """
        if ( not isinstance(numTR, int) ):
            raise ValueError ("selectTR argument must be an integer \r\n" "passed argument is :"+ type(numTR))
        cmd = ("SELECT " +str(numTR))
        return  self._writeReadAndVerify(cmd , "executed")
    
    def listInstalledTr(self) -> dict[str, str]:
        '''
        attempts to communicate with transient recorder with adresse 0 .. 15 and lists 
        all installed transient recorders.

        :raises RuntimeError: if no transient recorder is detected 

        :returns: dictionary containing information about installed Transient recorder
        :rtype: {'TR0': '(not)installed', 'TR1': '(not)installed', 'TR2': '(not)installed',
                 'TR3': '(not)installed', ....................... 'TR15': '(not)installed'}
        
        '''

        self.selectTR(-1)
        for i in range (0,16): 
            self.selectTR(i)
            self.writeCommand("STAT?")
            resp = self.readResponse()
            key = "TR" + str(i)
            if (resp.find("Shots") >= 0):
                self.__MaxTrNumber += 1
                self.__TrDict[key] = "installed"
            else:
                self.__TrDict[key] = "not installed"
        if self.__MaxTrNumber > 0 :
            return self.__TrDict
        else:
            raise RuntimeError ("no TR detected")
            return 
        

    def multiplyBinwidth(self, multiplier: int) -> str: 
        '''
        Multiply the the transient recorder base binwidth by ``multiplier``. 
        This will reduce the range resolution by actually reducing the sampling rate of 
        the transient recorder before the data summation. 
        multiplier possible value are between  0, 1, 2 ,4, 8, 16, 32, 64, 128. 

        :param deviceNumber: transient recorder adresse
        :type deviceNumber: int 

        :param multiplier: possible value are   0, 1, 2 ,4, 8, 16, 32, 64, 128.
        :param int:  
        '''

        if (not self._isPowerofTwo(multiplier)):
            raise ValueError ('\r\n multiplier must be 0 or a power of 2, possible value are 0, 1, 2 ,4, 8, 16, 32, 64, 128. Passed argument is :'+ str(multiplier))
        resp = self._setFreqDivider(multiplier)
        return resp 
    
    def getActualBinwidth(self, deviceNumber: int, hardwareInfos) -> float:
        self.selectTR(deviceNumber)
        freqDividerExponent = int (self._getFreqDivider().split(" ")[1])
        actualBinwidth = hardwareInfos[deviceNumber]['binWidth'] * (1<<freqDividerExponent)
        self.selectTR(-1)
        return actualBinwidth
    
    def configureHardware(self, Config: 'licel_Config.Config') -> None:
        """
        Configure the active transient recorders hardware as specified in config. \r\n
            currently configuers following parameters :
            - Threshold mode \r\n
            - Pretrigger \r\n
            - Discriminator level \r\n
            - Frequency divider \r\n
            - Input range \r\n
            - Max shots \r\n
            - Block global trigger. 

        :param Config: holds the acquisition configuration information
        :type Config: Licel.licel_acq.Config()
        
        :returns: None
        """
        #TODO - add more configuration to the hardware

        if not Config.TrConfigs :
            raise RuntimeError("Config file does not contain any transient recorder configuration.")
        for trConfig in Config.TrConfigs:
            transientIsActive = False
            for key in  trConfig.analogueEnabled:
                if (trConfig.analogueEnabled[key] == True  
                    or trConfig.pcEnabled[key]    == True) :
                        transientIsActive = True
            if transientIsActive == True :
                print(self.selectTR(trConfig.nTransientRecorder))
                print(self.setSlaveMode())
                print(self.clearMemory())
                print(self.setDiscriminatorLevel(trConfig.discriminator))
                print(self.disablePretrigger() if trConfig.pretrigger == 0 else self.enablePretrigger())
                if trConfig.threshold != 0 :
                    print(self.setThresholdMode("ON"))
                if trConfig.threshold == 0 :
                    print(self.setThresholdMode("OFF"))
                if trConfig.shotLimit != 0 :
                    print(self.setMaxShots(trConfig.shotLimit))
                nRange_str = "-"+ str(trConfig.nRange) +"mV"
                print(self.setInputRange(nRange_str))
                print(self.multiplyBinwidth(trConfig.freqDivider))
                self.__configureBlockGlobalTrigger__(trConfig)

        self.selectTR(-1)
        self._getTrHardwareInfo(Config)

        return 
    
        
    def __configureBlockGlobalTrigger__(self, trConfig: 'licel_Config.TrConfig') -> None:
        print(self.unblockRackTrigger())
        if trConfig.blockedTrig["A"]:
            print(self.blockRackTrigger("A"))
        if trConfig.blockedTrig["B"]:
            print(self.blockRackTrigger("B"))
        if trConfig.blockedTrig["C"]:
            print(self.blockRackTrigger("C"))
        if trConfig.blockedTrig["D"]:
            print(self.blockRackTrigger("D"))

    def _getTrHardwareInfo(self, Config: 'licel_Config.Config') -> None:
        '''
        get the transient hardware description from each active transient recorder in the 
        configuration.
        Writes the Hardware Information internally in `self.hardwareInfos`  

        :param Config: system configuration
        :type Config: Licel.licel_acq.Config()
        
        :returns: None
        '''

        for trConfig in Config.TrConfigs:
            transientIsActive = False
            for key in  trConfig.analogueEnabled:
                if (trConfig.analogueEnabled[key] == True  
                    or trConfig.pcEnabled[key]    == True) :
                        transientIsActive = True
            if transientIsActive == True :
                self.selectTR(trConfig.nTransientRecorder)
                self.hardwareInfos[trConfig.nTransientRecorder] = self.TRtype()
        self.selectTR(-1)
        return 
    
    def MPushStartFromConfig(self, shots: int, Config: 'licel_Config.Config') -> str:
        '''
        Starts the MPUSH acquisition mode from configuration.
        Internally this function will: 
        
            - Get the timestamp endianness \r\n
            - Get hardware information for each active transient recorder in Config. \r\n
            - Calculate the expected number of bytes to be received. \r\n
            - Generate the MPUSH command depending on the Config.   \r\n
            - Sends the generated MPUSH command to the controller. \r\n
        
        :param shots: number of shots to be acquired 
        :type shots: int

        :param Config: system configuration
        :type Config: Licel.licel_acq.Config()

        :returns: ethernet controller response 
        :rtype: str 
        '''
        #TODO - is it a good idea to hide Config.setDatasetsCount() inside 
        #MPushStartFromConfig()
        
        self._getTimestampEndianness()
        self._setDatasetsCount(shots, Config)
        command = self._generateMPUSHCommandFromConfig(shots, Config) 
        print(command)
        return  self._writeReadAndVerify(command, "executed")
    
    def _generateMPUSHCommandFromConfig(self, shots: int, Config: 'licel_Config.Config') -> str: 
        """
        generate Mpush command from the Configuration ``Config``

        :param shots: number of shots to be acquired. 
        :type shots: int

        :param Config: system configuration
        :type Config: Licel.licel_acq.Config()

        :returns: Mpush command
        :rtype: str 
        """
        command = "MPUSH " + str(shots)
        for trConfig in Config.TrConfigs: 
            for key in trConfig.analogueEnabled: 
                if trConfig.analogueEnabled[key] == True: 
                    tmpCommandLSW = (' {device:2d} {numberToread} LSW {memory}'
                        .format (device = trConfig.nTransientRecorder,
                                numberToread = trConfig.analogueBins[key],
                                memory = key)) 
                    tmpCommandMSW = (' {device:2d} {numberToread} MSW {memory}'
                        .format (device = trConfig.nTransientRecorder,
                                numberToread = trConfig.analogueBins[key],
                                memory = key)) 
                    tmpCommandPHM = ""
                    if (shots > 32764  
                    and self.hardwareInfos[trConfig.nTransientRecorder]['ADC Bits'] == 16 ):

                        tmpCommandPHM = (' {device:2d} {numberToread} PHM {memory}'
                        .format (device = trConfig.nTransientRecorder,
                                numberToread = trConfig.analogueBins[key],
                                memory = key)) 
                        
                    command += tmpCommandLSW + tmpCommandMSW + tmpCommandPHM

            for key in trConfig.pcEnabled: 
                if trConfig.pcEnabled[key] == True: 
                    TRnum = trConfig.nTransientRecorder
                    tmpCommandPC = (' {device:2d} {numberToread} PC {memory}'
                                    .format (device = trConfig.nTransientRecorder,
                                            numberToread = trConfig.pcBins[key],
                                            memory = key))
                    
                    tmpCommandPHM = ""
                    if ((shots > 4096 and self.hardwareInfos[TRnum]['PC Bits'] == 4)
                        or (shots > 1024 and self.hardwareInfos[TRnum]['PC Bits'] == 6)
                        or (shots > 256 and self.hardwareInfos[TRnum]['PC Bits'] == 8)): 
                        
                        tmpCommandPHM = (' {device:2d} {numberToread} PHM {memory}'
                        .format (device = trConfig.nTransientRecorder,
                                numberToread = trConfig.pcBins[key],
                                memory = key)) 
                    command += tmpCommandPC + tmpCommandPHM
        return command   
    
    def _setDatasetsCount(self, shots: int, Config: 'licel_Config.Config') -> None:
        """ 
        we parse the Configuration and calculate how many (raw)dataset 
        and the total number of bins we need to acquire. The number of shots and transient
        hardware information influences the number of raw data bytes we need to acquire. 
        this function update the value of ``exceptedByte`` and ``BufferSize`` in self.

        :param shots: number of shots the user wishes to acquire
        :type shots : int

        :returns: None
        """
        numDataSets = 0
        for myTrConfig in Config.TrConfigs: 
            for key in myTrConfig.analogueEnabled : 
                if myTrConfig.analogueEnabled[key] == True: 
                    Trnum = myTrConfig.nTransientRecorder
                    numDataSets += 1 #analogue data to be written to file. 
                    if ((shots > 4096) and (self.hardwareInfos[Trnum]['ADC Bits'] == 16)): 
                        #analogue data are formed from MSW LSW and PHM.  
                        self.__rawDataSets__ += 3 
                        self.totalnumBins += 3*myTrConfig.analogueBins[key]
                    else:
                        #analogue data are formed from MSW and LSW, 
                        self.__rawDataSets__ += 2 
                        self.totalnumBins += 2*myTrConfig.analogueBins[key]
                    
            for key in myTrConfig.pcEnabled: 
                if myTrConfig.pcEnabled[key] == True: 
                    Trnum = myTrConfig.nTransientRecorder
                    numDataSets += 1 #PC data to be written to file. 
                    if ((shots > 4096 and self.hardwareInfos[Trnum]['PC Bits'] == 4)
                        or (shots > 1024 and self.hardwareInfos[Trnum]['PC Bits'] == 6)
                        or (shots > 256 and self.hardwareInfos[Trnum]['PC Bits'] == 8)): 
                        #PC data are formed from PC and PHM. 
                        self.__rawDataSets__ += 2
                        self.totalnumBins += 2*myTrConfig.pcBins[key]
                    else:
                        #PC data are formed from PC only.
                        self.__rawDataSets__ += 1
                        self.totalnumBins += myTrConfig.pcBins[key]
            
            Config.numDataSets = numDataSets
            self.exceptedByte = (2*(self.totalnumBins + self.__rawDataSets__ + HEADEROFFSET))
            self.BufferSize = self.exceptedByte + NEXT_DELIMTER_OFFSET 

    
    def recvPushData(self) -> None:
        """
        read push/mpush data from the ethernet controller push port. \r\n
        used for reading push/mpush from transient recorder. \r\n
        fills ``self.pushBuffer``. 
        If after a certain time not data is recived, checks if counterpart is still 
        reachable by sending ``*IDN?`` on the command socket. 


        :raises: ConnectionResetError if the counter part closes the connection
        :raises: socketTimeout if counter part is unreachable
        :raises: ConnectionError if error is written.   
        """
        readSocket  = [self.PushSocket]
        writeSocket = [self.commandSocket]
        ErrorSocket = [self.commandSocket, self.PushSocket]
        while (len(self.pushBuffer) < self.BufferSize):
            (readableSocket,
             writableSocket,
             error_sockets) = select.select(readSocket, [], ErrorSocket, 5)
            if (readableSocket): 
                # Push socket is readable 
                # read from socket 
                packet = self.PushSocket.recv(self.BufferSize)
                if packet:
                    self.pushBuffer.extend(packet)
                # if socket is readable and packet is empty
                # this means we received a FIN from our counter part
                else : 
                    raise ConnectionResetError ("\nPush connection was closed by the remote host.")
            else:
                (readableSocket,
                writableSocket,
                error_sockets) = select.select([], writeSocket, ErrorSocket, 2)    
                if(writableSocket):
                    # command socket is writable 
                    # get id to check if connection is still alive.
                    # if connection is broken a timeout will be raised
                    self.getID() 
                if(error_sockets):
                    raise ConnectionError
        return 
    
    def getID(self) -> str:
        ''' Get the identification string from the controller 
        
        :returns: ethernet controller identification number
        :rtype: str  
        '''    
        return  self._writeReadAndVerify("*IDN?", " ")
    
    def _getTimestampEndianness(self) -> None:
        Idn = self.getID()
        if (Idn.find("ColdFireEthernet") != -1) : 
            self.bigEndianTimeStamp = True 