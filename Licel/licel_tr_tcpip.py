from Licel import licel_tcpip as TCP
from types import MappingProxyType
import time
import queue


### QUESTION EH : 
# in def setMaxBins(self, numMaxBins : int) -> str:  what is the permissable maxbin ??? 
# 

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


TRHardwareInfo_default = { 'ADC Bits' : 12, 'PC Bits' : 4, 'FIFOLength': 16384, 'binWidth' : 7.5,
                'ID' :0, 'HWCAP' : 0, 'binShift': 3.0, 'raw':0}

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


class licelTrTCP(TCP.licelTCP):
    TRHardwareInfo = {
    'ADC Bits' : 12,
    'PC Bits' : 4,
    'FIFOLength': 16384,
    'binWidth' : 7.5,
    'ID' :0,
    'HWCAP' : 0,
    'binShift': 3.0,
    'raw':0
    }


    def __init__(self, ip : str, port : int) -> None:
        super().__init__(ip, port)
        self.state = { "memory" : MEMORY['MEM_A'] , "recording": False , "acquisitionState": False    }
        
    def getID(self) -> str:
        ''' Get the identification string from the controller '''
        self.writeCommand("*IDN?")
        return self.readResponse() 
    
    def getCapabilities(self) -> str:
        '''
        Get the available subcomponents of the controller like:
        TR  - for controlling transient recorder \r\n
        APD - for APD remote control \r\n
        PMT - for PMT remote control \r\n
        TIMER - for the trigger timing controller \r\n
        CLOUD - for transient recorder controller cloud mode \r\n
        BORE  - Boresight alignment system \r\n
        '''
        self.writeCommand("CAP?")
        return self.readResponse() 
    
    def getMilliSecs(self) -> str:
        ''' Requests the millisecond timer value of the controller '''
        self.writeCommand("MILLISEC?")
        return self.readResponse() 
    
    def getStatus(self) -> list [bool,bool,str,int]:
        ''' Return the shot number for each memory, there is one clearing cycle at the start.'''
        acquisitionState =False
        recording = False
        memory = " "
        self.writeCommand("STAT?")
        resp= self.readResponse()
        assert resp.find("Shots") >=0, "\r\nLicel_TCPIP_GetStatus - Error 5765 : " + resp
        if resp.find("Armed") != -1:
            acquisitionState = True    
            recording = True
        if resp.find("MemB") != -1:
            memory = MEMORY["MEM_B"]
        shots = resp.split(" ")[1]
        return acquisitionState, recording, memory,int(shots)
    
    def setSlaveMode(self) -> str: 
        ''' Requests the millisecond timer value of the controller '''
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
        setThresholdMode sets the scale of the discriminator level \r\n
        In the low threshold mode the disciminator level 63 
        corresponds to -25mV while in the high threshold mode it corresponds to -100mV.
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
            raise ValueError ('freqDivider argument must be in Range of 1 ... 128 \r\n passed argument is :'+ freqDivider)
        while(freqDivider > 1):
            freqDivider = freqDivider /2
            exponent +=1
        self.writeCommand("FREQDIV "+ str(exponent)+" 0")
        resp = self.readResponse()
        assert int (resp.split(" ")[1]) == exponent, "\r\nLicel_TCPIP_SetFreqDivider - Error 5102 :" + resp
        return resp
    
    def selectTR(self, numTR : int) -> str: 
        if ( not isinstance(numTR, int) ):
            raise ValueError ('selectTR argument must be an integer \r\n passed argument is :'+ type(numTR))
        self.writeCommand("SELECT " +str(numTR))
        resp = self.readResponse()
        assert resp.find("executed") >=0, "\r\nLicel_TCPIP_SelectTR - Error 5083 : " + resp
        return resp

    def TRtype(self) -> dict:
        '''
        Get transient recorder hardware information for the selected transient 
        recorder. Old TR produced before Oct. 2009 will not support this command 
        If this command is not supported default values  for a TR20-160 are filled in
        '''
        self.writeCommand("TRTYPE?")
        resp = self.readResponse()
        print(resp)
        if resp.find("TRTYPE ADC Bits") == -1:
            return TRHardwareInfo_default
         
        parsedResp = resp.split(" ")
        self.TRHardwareInfo["ADC Bits"] = int(parsedResp[3])
        self.TRHardwareInfo["PC Bits"] = int(parsedResp[6])
        self.TRHardwareInfo["FIFOLength"]= int(parsedResp[8])
        self.TRHardwareInfo["binWidth"] = float(parsedResp[10])
        self.TRHardwareInfo["ID"] = parsedResp[12]
        self.TRHardwareInfo["HWCAP"] = parsedResp[14]
        self.TRHardwareInfo["binShift"] = float(parsedResp[16])
        #self.TRHardwareInfo["raw"]= parsedResp[18]
        return self.TRHardwareInfo
    
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
    ##################################################################################################
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
    
    def multipleWaitForReady(self) -> str: 
        '''
        Wait until all devices returned from the armed state.
        '''
        self.writeCommand("MWAIT")
        resp = self.readResponse()
        assert resp.find("MWAIT executed") >=0, "\r\nLicel_TCPIP_MultipleWaitForReady - Error 5083 : " + resp
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
            command += (str(item) + " ")
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
            raise ValueError ('setPushMode memory must be :'+ str(MEMORY.keys())+'\r\n passed argument is :'+ memory)
        if (not (dataType in PUSHMODETYPE.keys())):
            raise ValueError ('setPushMode dataType must be :' + str(PUSHMODETYPE.keys())+'\r\n passed argument is :'+ dataType)
        
        command = "PUSH " + str(shots) + " " + str(numberToRead) +" "+ PUSHMODETYPE[dataType] +" "+ MEMORY[memory]
        self.openPushConnection()
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
    
    def MPushStart(self, shots: int , TRList: list[int], dataType: list[str], 
                   numberToRead: list[int], Memories: list[str], numDataSets: int ) -> str: 
        
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
        acquisitionState =False
        recording = False
        memory = " "
        start = (time.time()*1000)
        while (time.time()*1000) < start + delay:
            acquisitionState, recording, memory,shots =self.getStatus()
            if not acquisitionState :
                return 
        return  " Timeout"