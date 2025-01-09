#! python3.10
'''
Copyright ©: Licel Gmbh 
The licelTCP class  Holds methods for handling the sockets with the ethernet controller,
detecting the number of transient recorders present and
starting the MPUSH acquisition from configuration 
'''

import socket
from Licel import licel_tr_tcpip, photomultiplier, TCP_util
import select
import time



HEADEROFFSET = 3 # 3* 2 byte = 6byte represents first delimiter xff xff + timestamp 
NEXT_DELIMTER_OFFSET = 2 # 2 byte representing the next delimiter xff xff
class EthernetController(TCP_util.util): 

    __MaxTrNumber = 0
    __TrDict = {}
    #:
    Tr = licel_tr_tcpip.TransientRecorder
    #:
    pmt = photomultiplier.photomultiplier

    bigEndianTimeStamp = False
    #: a dictionary  containing hardware info for each active transient recorder.
    #  dict{Tr_num : dict{'ADC Bits' : ' ', 'PC Bits' : ' ' , 'FIFOLength': ' ' ,
    #                     'binWidth' : ' ', 'ID' : ' ', 
    #                     'HWCAP' : ' ', 'binShift': ' ', 'raw': ' '}}
    hardwareInfos = {}
    pushBuffer = bytearray()

    #: holds the total number of raw datasets to be read, MSW LSW PC PHM   
    __rawDataSets__ = 0  
    #: holds the total number of bins to be read.
    totalnumBins = 0 
    #: Buffer size to receive MPUSH data
    BufferSize = 0 
    #: number of byte expected to be received for a complete data set      
    exceptedByte = 0    

    
    def __init__(self, ip: str, port : int) -> None:
        self.ip = ip
        self.port = port 
        self._renewSockets()


    def _renewSockets(self): 
        TCP_util.util.__init__(self, self.ip, self.port)
        self.Tr = licel_tr_tcpip.TransientRecorder(self.commandSocket, self.PushSocket,
                                                   self.killsock, self.sockFile )
        self.pmt = photomultiplier.photomultiplier(self)

        

    def openConnection(self) -> None:
        """
        Open connection to the command socket
        
        :raises TimeoutError: attempted connection but controller did not respond. 
            Possible causes, controller is not connected to network or 
            controller is already connected to other device
        
        :returns: None
        """
        try:
            self.commandSocket.connect((self.ip, self.port))
        except socket.timeout: 
            raise socket.timeout ("\nConnection timeout to IP: "+self.ip + 
                                  " PORT: "+str(self.port))
        return
        
    def shutdownConnection(self) -> None:
        """
        close connection to the command socket
    
        :returns: None
        """ 
        self.commandSocket.shutdown(socket.SHUT_RDWR)
        self.commandSocket.close()
        return
    
    def openPushConnection(self) -> None:
        """
        Open connection to the push socket
        
        :raises TimeoutError: attempted connection but controller did not respond. 
            Possible causes, controller is not connected to network or 
            controller is already connected to other device
        
        :returns: None
        """
        try:
            self.PushSocket.connect((self.ip, self.pushPort))
        except socket.timeout: 
            raise socket.timeout ("\nConnection timeout to IP: "+self.ip + 
                                  " PORT: "+str(self.pushPort))
        return
        
    def shutdownPushConnection(self) -> None: 
        """
        close connection to the push socket
    
        :returns: None
        """ 
        self.PushSocket.shutdown(socket.SHUT_RDWR)
        self.PushSocket.close()
        return
    
    def killSocket(self) -> None : 
        """
        Method to be used when controller is not responding. 
        This will attempt to connect on the controller ``kill port`` and asks the 
        controller to close all it's open connection. 
        This should act as a soft reset and we will be able to established a new connection 
        with the controller   

        used internally in the reconnect mechanisms.

        :raises Socket.timeout: if unable to connect to kill port.

        :returns: None
        """ 
        try:
            self.killsock.connect((self.ip, self.killPort))
            self.killsock.send("KILL SOCKETS Administrator\r\n".encode())
        except socket.timeout: 
            raise socket.timeout ("\nKill socket Connection timeout to IP: "+self.ip + 
                                  " PORT: "+str(self.killPort))
        return
        
    def getID(self) -> str:
        ''' Get the identification string from the controller 
        
        :returns: ethernet controller identification number
        :rtype: str  
        '''    
        return  self._writeReadAndVerify("*IDN?", " ")

    
    def getCapabilities(self) -> str:
        '''
        Get the available subcomponents of the ethernet controller like:
            - TR - for controlling transient recorder \r\n
            - APD - for APD remote control \r\n
            - PMT - for PMT remote control \r\n
            - PMTSPI - for controller PMT high voltage module via SPI \r\n
            - TIMER - for the trigger timing controller \r\n
            - CLOUD - for transient recorder controller cloud mode \r\n
            - BORE  - Boresight alignment system \r\n

        :returns: ethernet controller subcomponents
        :rtype: str
        '''
        return  self._writeReadAndVerify("CAP?", "CAP")

    
    def getMilliSecs(self) -> str:
        '''
         Requests the millisecond timer value of the controller 
        
        :returns: millisecond timer value of the controller
        :rtype: str 
        '''
        return  self._writeReadAndVerify("MILLISEC?", " ")

        
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


    def listInstalledTr(self) -> licel_tr_tcpip.TransientRecorder:
        '''
        attempts to communicate with transient recorder with adresse 0 .. 15 and lists 
        all installed transient recorders.

        :raises RuntimeError: if no transient recorder is detected 

        :returns: dictionary containing information about installed Transient recorder
        :rtype: {'TR0': '(not)installed', 'TR1': '(not)installed', 'TR2': '(not)installed',
                 'TR3': '(not)installed', ....................... 'TR15': '(not)installed'}
        
        '''
#       TODO CHANGE TYPE HINT, method doe not return TransientRecorder object     
#       [ ]  I dont think that the object model ethernetcontroller should return TR object. 
#       [x]  now the ethernet controller class contains transient recorder as an object
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
    
    def _generateMPUSHCommandFromConfig(self, shots, Config): 
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
    
    def MPushStartFromConfig(self, shots :int , Config):
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


    def _getTrHardwareInfo(self, Config) -> dict[dict]:
        '''
        get the transient hardware description from each active transient recorder in the 
        configuration.
        Writes the Hardware Information internally in `self.hardwareInfos`  

        :param Config: system configuration
        :type Config: Licel.licel_acq.Config()
        
        :returns: None
        '''

        #TODO fix documentations 
        for trConfig in Config.TrConfigs:
            transientIsActive = False
            for key in  trConfig.analogueEnabled:
                if (trConfig.analogueEnabled[key] == True  
                    or trConfig.pcEnabled[key]    == True) :
                        transientIsActive = True
            if transientIsActive == True :
                self.selectTR(trConfig.nTransientRecorder)
                self.hardwareInfos[trConfig.nTransientRecorder] = self.Tr.TRtype()
        self.selectTR(-1)
        return 

    def MPushStop(self): 
        """ 
        stops the push/mpush mode. Internally it sends a ``SLAVE`` command.
        for more information: https://licel.com/manuals/ethernet_pmt_tr.pdf#TCPIP.SLAVE
        :raises Exception: if the stop command is not executed.

        :returns: Controller response.
        :rtype: str 
        """
        return self.Tr.setSlaveMode()
         
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
    
    def reconnection(self,ConfigInfo):
        reconnectAttempt = 0
        MAXRECONNECTIONATTEMPT = 5
        self.shutdownConnection()
        self.shutdownPushConnection()
        while (reconnectAttempt < MAXRECONNECTIONATTEMPT):
            try:
                print("Reconnect attempt number ",reconnectAttempt)
                reconnectAttempt += 1
                self.killSocket()
                self._renewSockets()
                self.openConnection()
                self.openPushConnection()
                self.listInstalledTr()   
                self.configureHardware(ConfigInfo)  
                self.pushBuffer = bytearray()
                print("Reconnection Successful")
                break
            except:
                if (reconnectAttempt > MAXRECONNECTIONATTEMPT):
                    raise RuntimeError ("\nFailed to reconnect to "+self.ip+" after 5 attempts") 
                else : 
                    continue
    

    
    def _getTimestampEndianness(self):
        Idn = self.getID()
        if (Idn.find("ColdFireEthernet") != -1) : 
            self.bigEndianTimeStamp = True 

    def configureHardware (self, Config) :
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
                print(self.Tr.setSlaveMode())
                print(self.Tr.clearMemory())
                print(self.Tr.setDiscriminatorLevel(trConfig.discriminator))
                print(self.Tr.disablePretrigger() if trConfig.pretrigger == 0 else self.enablePretrigger())
                if trConfig.threshold != 0 :
                    print(self.Tr.setThresholdMode("ON"))
                if trConfig.threshold == 0 :
                    print(self.Tr.setThresholdMode("OFF"))
                if trConfig.shotLimit != 0 :
                    print(self.Tr.setMaxShots(trConfig.shotLimit))
                nRange_str = "-"+ str(trConfig.nRange) +"mV"
                print(self.Tr.setInputRange(nRange_str))
                print(self.multiplyBinwidth(trConfig.freqDivider))
                self.__configureBlockGlobalTrigger__(trConfig)

        self.selectTR(-1)
        self._getTrHardwareInfo(Config)

        return 
    
    def __configureBlockGlobalTrigger__(self, trConfig):
        print(self.Tr.unblockRackTrigger())
        if trConfig.blockedTrig["A"]:
            print(self.Tr.blockRackTrigger("A"))
        if trConfig.blockedTrig["B"]:
            print(self.Tr.blockRackTrigger("B"))
        if trConfig.blockedTrig["C"]:
            print(self.Tr.blockRackTrigger("C"))
        if trConfig.blockedTrig["D"]:
            print(self.Tr.blockRackTrigger("D"))

    def _setDatasetsCount(self, shots, Config):
        """ 
        we parse the Configuration and calculate how many (raw)dataset 
        and the total number of bins we need to acquire. The number of shots and transient
        hardware information influences the number of raw data bytes we need to acquire. 
        this function update the value of ``exceptedByte`` and ``BufferSize`` in self.

        :param shots: number of shots the user wishes to acquire
        :type shots : int

        :param TRHardwareInfos: list contains hardware information for each detected 
        transient recorder
        :type TRHardwareInfos: dict{Tr_num : dict{'ADC Bits' : ' ', 'PC Bits' : ' ' ,
        FIFOLength': ' ', binWidth' : ' ', 'ID' : ' ', 'HWCAP' : ' ', 'binShift': ' ',
        'raw': ' '}}

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
    

    def getActualBinwidth(self, deviceNumber):
        self.selectTR(deviceNumber)
        freqDividerExponent = int (self.Tr._getFreqDivider().split(" ")[1])
        actualBinwidth = self.hardwareInfos[deviceNumber]['binWidth'] * (1<<freqDividerExponent)
        self.selectTR(-1)
        return actualBinwidth
    
    def multiplyBinwidth(self,  multiplier): 
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

        if (not self.Tr._isPowerofTwo(multiplier)):
            raise ValueError ('\r\n multiplier must be 0 or a power of 2, possible value are 0, 1, 2 ,4, 8, 16, 32, 64, 128. Passed argument is :'+ str(multiplier))
        resp = self.Tr._setFreqDivider(multiplier)
        return resp 

