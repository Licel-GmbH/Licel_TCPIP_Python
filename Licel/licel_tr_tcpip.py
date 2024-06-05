from Licel import TCP_util
from types import MappingProxyType
import time
import queue
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


# Block rack trigger accepted string 
BLOCKTRIGGER = {"BLOCK A", "BLOCK B", "BLOCK C", "BLOCK D"}



class licelTrTCP(TCP_util.util):

    Tr_number = " "

    def __init__(self, sock, pushSock, killSock, sockF ) -> None:
#        self.Tr_number = TR_num
        self.state = { "memory" : MEMORY['MEM_A'] ,
                       "recording": False , "acquisitionState": False}
        self.commandSocket  = sock
        self.PushSocket     = pushSock 
        self.sockFile       = sockF
        self.killsock       = killSock
    
    def getStatus(self) -> list [bool,bool,str,int]:
        ''' Return the shot number for each memory, there is one clearing cycle at the start.'''
        acquisitionState =False
        recording = False
        memory = "MEM_A "
        self.writeCommand("STAT?")
        resp= self.readResponse()
        assert resp.find("Shots") >=0, "\r\nLicel_TCPIP_GetStatus - Error 5765 : " + resp
        if resp.find("Armed") != -1:
            acquisitionState = True    
            recording = True
        if resp.find("MemB") != -1:
            memory = "MEM_B"
        shots = resp.split(" ")[1]
        return acquisitionState, recording, memory,int(shots)
    
    def setSlaveMode(self) -> str: 
        ''' Set slave mode. end push mode '''
        self.writeCommand("SLAVE")
        resp = self.readResponse() 
        assert resp == "SLAVE executed\n", "\r\nLicel_TCPIP_SetSlaveMode - Error 5085 :" + str(resp.encode())
        return resp
    
    def clearMemory(self) -> str: 
        ''' Clear both memories (A and B) of the previously selected device.'''
        self.writeCommand("CLEAR")
        resp= self.readResponse()
        assert resp == "CLEAR Memory executed\n", "\r\nLicel_TCPIP_ClearMemory - Error 5092: " + resp
        return resp
    
    def multipleClearMemory(self) -> str:
        self.writeCommand("MCLEAR")
        resp = self.readResponse()
        assert resp == "MCLEAR executed\n", "\r\nLicel_TCPIP_MultipleClearMemory - Error 5080 : " + resp
        return resp
    
    def blockRackTrigger(self, trig: str) -> str:
        mode ="BLOCK " + trig
        if (not (mode in BLOCKTRIGGER )) :
            raise ValueError ('Argument can only be "A", "B", "C", "D"')
        self.writeCommand(mode)
        resp = self.readResponse()
        assert resp == "BLOCK executed\n", "\r\nLicel_TCPIP_BlockRackTrigger - Error 5108 : " + resp
        return resp
    
    def unblockRackTrigger(self) -> str:
        self.writeCommand("BLOCK OFF")
        resp = self.readResponse()
        assert resp == "BLOCK executed\n", "\r\nLicel_TCPIP_UnblockRackTrigger - Error 5108 : " + resp
        return resp
    
    def enablePretrigger(self) -> str:
        '''
        Enable the pretrigger for a selected TR. In TR20-16bit this will be 128 bins 
        long shipped till 2018, since 2018 the TR40-16bit-3U will have 1/16 of the 
        trace length. This means for a 16k the pretrigger will be 1024 bins long. 
        The TR will power up with pretrigger off.  
        TR devices supporting pretrigger indicate it by bit 3 in the HWCAP field of 
        the TRTYPE? command.
        '''
        self.writeCommand("PRETRIG 1")
        resp = self.readResponse()
        assert resp == "PRETRIG executed\n" , ("\r\nLicel_TCPIP_PreTrigger - Error 5109 : " + resp)
        return resp
    
    def disablePretrigger(self) -> str:
        ''' Disable the pretrigger for a selected TR'''
        self.writeCommand("PRETRIG 0")
        resp= self.readResponse()
        assert resp == "PRETRIG executed\n" , ("\r\nLicel_TCPIP_PreTrigger - Error 5109 : " + resp)
        return resp
    
    def startAcquisition(self) -> str :
        ''' Start the currently selected transient recorder.'''
        self.writeCommand("START")
        resp = self.readResponse()
        assert resp.find("START executed") >=0, "\r\nLicel_TCPIP_SingleShot - Error 5095 :" + resp 
        return resp
    
    def stopAcquisition(self) -> str: 
        ''' Stops the currently selected transient recorder.'''
        self.writeCommand("STOP")
        resp = self.readResponse()
        assert resp.find("STOP executed") >=0, "\r\nLicel_TCPIP_StopAcquisition - Error 5094: " + resp
        return resp
    
    def setShotLimit(self, limit : str) -> str:
        '''
        Switch between 4k and 64k maxshots. 
        permissable arguments are : \r\n
        limit = str "64K" \r\n
        limit = str "4K"  \r\n
        '''
        if (not ((limit != '64K') ^ (limit != '4K'))):
            raise ValueError ('setShotLimit argument can only be "64K", "4K" ')
        self.writeCommand(("LIMIT "+ limit))
        resp = self.readResponse()
        assert resp == "LIMIT executed\n", "\r\nLicel_TCPIP_SetShotLimit - Error 5100 : " + resp
        return resp
    
    def setMaxBins(self, numMaxBins : int) -> str:
        '''
        Set the maximum  shotnumber of the TR unit if the Memory DIP Switch 5 is in 
        the ON position. This allows to adapt the TR unit better to the repetition 
        rate and tracelength requirements.
        '''
        #Check validity of maxbins ??
        self.writeCommand(("SETMAXBINS "+ str(numMaxBins)))
        resp = self.readResponse()
        assert resp == "SETMAXBINS executed\n", "\r\nLicel_TCPIP_SetMaxBins - Error 5110 : " + resp
        return resp
    

    def setMaxShots(self, maxShots : int) ->str:
        '''
        Set the maxmimum  shotnumber of the TR this can be an arbitrary number 
        between 2 and 65335, the startup default is 4096. This will work with newer 
        TR. If this command fails and the unit claims that it supports 64k shots then
        Licel_TCPIP_SetShotLimit will work.
        '''        
        if (not (maxShots <= 65335 and maxShots >= 2)):
            raise ValueError ('setMaxShots argument must be in range of (2 ... 65335) ')
        self.writeCommand(("SETMAXSHOTS "+ str(maxShots)))
        resp = self.readResponse()
        assert resp.find("SETMAXSHOTS executed") >=0, "\r\nLicel_TCPIP_SetMaxShots - Error 5103 : " + resp
        return resp
    
    def singleShot(self) -> str:
        '''
        Start the currently selected transient recorder.
        '''
        self.writeCommand(("SINGLE"))
        resp = self.readResponse()
        assert resp == "SINGLE executed\n", "\r\nLicel_TCPIP_SingleShot - Error 5091 : " + resp
        return resp

    def setThresholdMode(self, thresholdMode : str) -> str:
        '''
        Sets the damping state to either on or off.
        If a value of 1 is sent then damping is turned on. If a value
        of 0 is sent, the damping is turned off
        '''
        if (not ((thresholdMode != 'ON') ^ (thresholdMode != 'OFF'))):
            raise ValueError ('setThresholdMode argument must be either "ON" or "OFF" \r\n passed argument is :'+thresholdMode)
        if (thresholdMode == 'ON'):
            self.writeCommand(("THRESHOLD 1"))
        if (thresholdMode == 'OFF'):
            self.writeCommand(("THRESHOLD 0"))
        resp = self.readResponse()
        assert resp.find("Damping") >=0, "\r\nLicel_TCPIP_SetThresholdMode - Error 5098 : " + resp
        return resp
    
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
        self.writeCommand(("RANGE "+str(INPUTRANGE[Range])))
        resp = self.readResponse()
        assert resp.find("set to") >=0, "\r\nLicel_TCPIP_SetInputRange - Error 5097 : " + resp
        return resp

    def getFreqDivider(self) -> str:
        '''
        Retrieve the frequency divider, the values are valid only for units 
        supporting this feature, to get the actual binwidth multiply the binwidth 
        returned by TRTYPE with the freqDivider.\r\n
        The  binwidth reported by 
        TRType needs then to be multiplied with FreqDivider
        '''
        self.writeCommand("FREQDIV?")
        resp = self.readResponse()
        return resp
    
    def setFreqDivider(self, freqDivider : int) -> str:
        '''
        Set the frequency divider, this will have effect only on units  
        supporting this feature, it changes the sampling rate before the summation 
        of the data.
        '''
        exponent = 0
        if (freqDivider > 128 or freqDivider < 1):
            raise ValueError ('freqDivider argument must be in Range of 1 ... 128 \r\n passed argument is :'+ str(freqDivider))
        while(freqDivider > 1):
            freqDivider = freqDivider /2
            exponent +=1
        self.writeCommand("FREQDIV "+ str(exponent)+" 0")
        resp = self.readResponse()
        assert int (resp.split(" ")[1]) == exponent, "\r\nLicel_TCPIP_SetFreqDivider - Error 5102 :" + resp
        return resp
    
    def TRtype(self) -> dict:
        '''
        Get transient recorder hardware information for the selected transient 
        recorder. Old TR produced before Oct. 2009 will not support this command 
        If this command is not supported default values  for a TR20-160 are filled in

        :returns: hardware info
        :rtype: 
        '''
        tempTRHardwareInfo = {}
        self.writeCommand("TRTYPE?")
        resp = self.readResponse()
        if resp.find("TRTYPE ADC Bits") == -1:
            return TRHardwareInfo_default
         
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
    
    def selectTR(self, numTR : int) -> str: 
        """ 
        Select the transient recorder to communicate with 

        :param numTr: transient recorder address. 0 .. 15
        :type param: int 
        """
        if ( not isinstance(numTR, int) ):
            raise ValueError ('selectTR argument must be an integer \r\n passed argument is :'+ type(numTR))
        self.writeCommand("SELECT " +str(numTR))
        resp = self.readResponse()
        return resp
    
    def configureHardware (self, Config) :
        """
        Configure the active transient recorders hardware as specified in config. 

        :param Config: holds the acquisition configuration information
        :type Config: Licel.licel_acq.Config()
        """
        for trConfig in Config.TrConfigs:
            transientIsActive = False
            for key in  trConfig.analogueEnabled:
                if (trConfig.analogueEnabled[key] == True  
                    or trConfig.pcEnabled[key]    == True) :
                        transientIsActive = True
            if transientIsActive == True :
                print(self.selectTR(trConfig.nTransientRecorder))
                print(self.setSlaveMode())
                print(self.setDiscriminatorLevel(trConfig.discriminator))
                print(self.disablePretrigger() if trConfig.pretrigger == 0 else self.enablePretrigger())
                if trConfig.threshold != 0 :
                    print(self.setThresholdMode("ON"))
                if trConfig.threshold == 0 :
                    print(self.setThresholdMode("OFF"))
                if trConfig.freqDivider != 0 :
                    print(self.setFreqDivider(trConfig.freqDivider))
                if trConfig.shotLimit != 0 :
                    print(self.setMaxShots(trConfig.shotLimit))
                nRange_str = "-"+ str(trConfig.nRange) +"mV"
                print(self.setInputRange(nRange_str))
        self.selectTR(-1)
        return 
    
    def continueAcquisition(self) -> str: 
        '''
        Continue the recording process for the previously specified device without 
        reinitializing the memory.
        '''
        self.writeCommand("CONTINUE")
        resp = self.readResponse()
        assert resp.find("CONTINUE executed") >=0, "\r\nLicel_TCPIP_ContinueAcquisition - Error 5093 : " + resp
        return resp
    

    def readData(self, numberToRead : int) -> bytearray :
        '''
        Wait until the the number of scans defined by Number to Read is available
        and reads them or returns a timeout error if the timeout ms is exceeded.
        Read binary data into a byte array. Transient recorder data is internally
        16bits wide so for every data point two bytes need to be fetched
        '''
        return self.recvall(numberToRead)

    def requestData(self, device : int, numberToRead : int,
                    datatype : str, memory : str ) -> str :
        '''
        Requesting the raw data sets ( analog LSW, analog MSW or photon counting) from
        the specified device for later read.
        '''
        if (not (datatype in DATASETSTYPE.keys())):
            raise ValueError ('requestDataSet datatype can be :'+ str(DATASETSTYPE.keys())+'\r\n passed argument is :'+ datatype)
        if (not (memory in MEMORY.keys())):
            raise ValueError ('requestDataSet memory can be :'+ str(MEMORY.keys())+'\r\n passed argument is :'+ memory)
        commadTosend = "DATA? " + str(device) + " " + str(numberToRead) +" "+ DATASETSTYPE[datatype] +" "+ MEMORY[memory]
        self.writeCommand(commadTosend)

    def getDataSet(self, device : int, numberToRead : int,
                    datatype : str, memory : str ) -> bytearray :
        '''
        Reading the raw data sets ( analog LSW, analog MSW or photon counting) from
        the specified device.
        '''
        self.requestData(device, numberToRead, datatype, memory)
        data = self.readData(numberToRead)
        return data
    
    def getShotsAB(self) -> str:
        '''
        Return the shot number for each memory, there is one clearing cycle at the start.
        '''
        self.writeCommand("SHOTAB?")
        resp = self.readResponse()
        assert resp.find("SHOTAB") >=0, "\r\nLicel_TCPIP_GetShotsAB - Error 5105 : " + resp
        return resp
    
    def getMultipleShotsAB(self) -> str: 
        '''
         Return the shotnumber for each memory, there is one clearing cycle at the start.
        '''
        self.writeCommand("MSHOTSAB?")
        resp = self.readResponse()
        assert resp.find("MSHOTS") >=0, "\r\nLicel_TCPIP_GetMultipleShotsAB - Error 5106 : " + resp
        return resp

    def getMultipleShots(self) -> str: 
        '''
        Return the shotnumber for each memory, there is one clearing cycle at the start.
        '''
        self.writeCommand("MSHOTS?")
        resp = self.readResponse()
        assert resp.find("MSHOTS") >=0, "\r\nLicel_TCPIP_GetMultipleShots - Error 5106 : " + resp
        return resp

    def multipleClearMemory(self) -> str:
        '''
        Clears both memories (A and B) of the currently selected devices.
        '''
        self.writeCommand("MCLEAR")
        resp = self.readResponse()
        assert resp.find("MCLEAR executed") >=0, "\r\nLicel_TCPIP_MultipleClearMemory - Error 5080 : " + resp
        return resp
    
    def multipleContinueAcquisition(self) -> str:
        '''
        The acquisition process of the selected multiple devices will be restarted
        without clearing their memories.
        '''
        self.writeCommand("MCONTINUE")
        resp = self.readResponse()
        assert resp.find("MCONTINUE executed") >=0, "\r\nLicel_TCPIP_MultipleContinueAcquisition - Error 5080 : " + resp
        return resp
    
    def multipleStartAcquisition(self) -> str:
        '''
        The acquisition process will be started after the next received trigger for
        multiple devices
        '''
        self.writeCommand("MSTART")
        resp = self.readResponse()
        assert resp.find("MSTART executed") >=0, "\r\nLicel_TCPIP_MultipleStartAcquisition - Error 5086 : " + resp
        return resp
    
    def multipleStopAcquisition(self) -> str: 
        '''
        The acquisition process will be stoped after the next received trigger for
        multiple devices
        '''
        self.writeCommand("MSTOP")
        resp = self.readResponse()
        assert resp.find("MSTOP executed") >=0, "\r\nLicel_TCPIP_MultipleStopAcquisition - Error 5082 : " + resp
        return resp
    
    def multipleWaitForReady(self, miliSec) -> str: 
        '''
        Wait until all devices returned from the armed state.
        '''
        command = "MWAIT " + str(miliSec) 
        self.writeCommand(command)
        resp = self.readResponse()
        #assert resp.find("MWAIT executed") >=0, "\r\nLicel_TCPIP_MultipleWaitForReady - Error 5083 : " + resp
        return resp
    
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
        self.writeCommand(command)
        resp = self.readResponse()
        assert resp.find("executed") >=0, "\r\nLicel_TCPIP_SelectMultipleDevice - Error 5081 : " + resp
        return resp
    
    def setDiscriminatorLevel(self, discriminatorLevel:int ) -> str:
        '''
        Set the discriminator level between 0 and 63 for the selected transient
        recorders.
        '''
        if (discriminatorLevel <0 or discriminatorLevel > 63): 
            raise ValueError ('setDiscriminatorLevel discriminatorLevel must be in range 1 ... 63 \r\n passed argument is :'+ str(discriminatorLevel))
        command = "DISC " + str(discriminatorLevel)
        self.writeCommand(command)
        resp = self.readResponse()
        assert resp.find("set to") >=0, "\r\nLicel_TCPIP_SetDiscriminatorLevel - Error 5096 : " + resp
        return resp
    
    def setPushMode(self, shots: int, dataType:str, numberToRead: int, memory: str ) ->  str:
        if (not (memory in MEMORY.keys())):
            raise ValueError ('setPushMode memory must be :'+
                               str(MEMORY.keys())+'\r\n passed argument is :'+ memory)
        if (not (dataType in PUSHMODETYPE.keys())):
            raise ValueError ('setPushMode dataType must be :'+
                              str(PUSHMODETYPE.keys())+'\r\n passed argument is :'+
                                dataType)
        
        command =("PUSH " + str(shots) + " " + str(numberToRead) +
                  " "+ PUSHMODETYPE[dataType] +" "+ MEMORY[memory])
        #self.openPushConnection()
        self.writeCommand(command)
        resp = self.readResponse()
        assert resp.find("PUSH executed") >=0, "\r\nLicel_TCPIP_SetPushMode - Error 5096 : " + resp
        return resp
    
    def dataHandler(self,queue: queue, pushBuffer: bytearray):
        while self.run_PushThreads:
            if not queue.empty():
                pushBuffer.extend(queue.get())
        return
    
    def checkDelimiter(self, data) -> list[int]:
        '''
        return a list holding the positions of "\\xff\\xff" delimiter  
        last element of the returned list is -1 indicating that the delimiter is not found.
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

    def MPushStart(self, shots: int , TRList: list[int], dataType: list[str], 
                   numberToRead: list[int], Memories: list[str], numDataSets: int ) -> str: 
        '''
        starts MPUSH acquisition, this method is deprecated. 
        it is recommended to start MPUSH from a configuration file, 
        using the licelTCP.MPushStartFromConfig() method  
        '''
        assert len(TRList) == len(numberToRead) == len(Memories) == len(dataType)
        command = "MPUSH " + str(shots)
        for i in range(0 , numDataSets):
            if (not (dataType[i] in DATASETSTYPE.keys())):
                raise ValueError ('MPushStart datatype['+ i+']'+ 'can be :'+ str(DATASETSTYPE.keys())+'\r\n passed argument is :'+ dataType)
            if (not (Memories[i] in MEMORY.keys())):
                raise ValueError ('MPushStart Memories can be :'+ str(MEMORY.keys())+'\r\n passed argument is :'+ Memories)
            command += " "+str(TRList[i]) + " " + str(numberToRead[i]) + " " + DATASETSTYPE[dataType[i]] + " " + MEMORY[Memories[i]]
        print(command)
        self.writeCommand(command)
        resp = self.readResponse()
        assert resp.find("MPUSH executed") >=0, "\r\nLicel_TCPIP_Licel_TCPIP_MPushStart - Error 5111 : " + resp
        return resp
        
    def waitForReady(self,delay: int) -> str:
        """
        Waits for return of the device from the armed state. If the waiting time
        is longer than the time specified by delay than the device remains armed
        and will be return to the idle state with next reading of binary data

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
        return  " Timeout"
    

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
            mem_low_buffer  = self.getDataSet(device, bins + 1, "LSW", memory)   
            mem_high_buffer = self.getDataSet(device, bins + 1, "MSW", memory)
            mem_low   = numpy.frombuffer(mem_low_buffer,numpy.uint16)
            mem_high  = numpy.frombuffer(mem_high_buffer,numpy.uint16)
            mem_extra = numpy.zeros((bins))
            if shots > 4096 :
                mem_extra_buffer = self.getDataSet(device, bins + 1,"PHM", memory)
                mem_extra = numpy.frombuffer(mem_extra_buffer,numpy.uint16)
            return  dataParser.combine_Analog_Datasets_16bit(mem_low, mem_high, mem_extra)
        else : 
            mem_low_buffer  = self.getDataSet(device, bins + 1, "LSW", memory)   
            mem_high_buffer = self.getDataSet(device, bins + 1, "MSW", memory)
            mem_low  = numpy.frombuffer(mem_low_buffer,numpy.uint16)
            mem_high = numpy.frombuffer(mem_high_buffer,numpy.uint16)
            return dataParser.combine_Analog_Datasets(mem_low, mem_high)

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
        mem_low_buffer   = self.getDataSet(device, binsSqd + 1, "A2L", memory) 
        mem_high_buffer  = self.getDataSet(device, binsSqd + 1, "A2M", memory)
        mem_extra_buffer = self.getDataSet(device, binsSqd + 1, "A2H", memory) 
        mem_low   = numpy.frombuffer(mem_low_buffer, numpy.uint16)
        mem_high  = numpy.frombuffer(mem_high_buffer, numpy.uint16)
        mem_extra = numpy.frombuffer(mem_extra_buffer, numpy.uint16)

        return dataParser.combineAnalogSquaredData(mem_low, mem_high, mem_extra)

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
            mem_low_buffer   = self.getDataSet(device, bins + 1, "PC" , memory) 
            mem_extra_buffer = self.getDataSet(device, bins + 1 , "PHM",memory) 
            mem_low   = numpy.frombuffer(mem_low_buffer,numpy.uint16)
            mem_extra = numpy.frombuffer(mem_extra_buffer,numpy.uint16)
            return dataParser.convert_Photoncounting_Fullword(mem_low, mem_extra)

        else: 
            PUREPHOTON = 0
            mem_low_buffer   = self.getDataSet(device, bins + 1, "PC" , memory) 
            mem_low   = numpy.frombuffer(mem_low_buffer,numpy.uint16)
            return dataParser.convert_Photoncounting(mem_low, PUREPHOTON)

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
        mem_low_buffer   = self.getDataSet(device, binsSqd + 1, "P2L", memory) 
        mem_high_buffer  = self.getDataSet(device, binsSqd + 1, "P2M", memory)
        mem_low   = numpy.frombuffer(mem_low_buffer,numpy.uint16)
        mem_high  = numpy.frombuffer(mem_high_buffer,numpy.uint16)

        return dataParser.combine_Photon_Squared_Data(mem_low, mem_high)

    



