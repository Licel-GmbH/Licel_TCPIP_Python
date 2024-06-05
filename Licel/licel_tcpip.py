#! python3.10
'''
Copyright ©: Licel Gmbh 
The licelTCP class  Holds methods for handling the sockets with the ethernet controller,
detecting the number of transient recorders present and
starting the MPUSH acquisition from configuration 
'''

import socket
from Licel import licel_tr_tcpip, TCP_util

class licelTCP(TCP_util.util): 

    MaxTrNumber = 0
    def __init__(self, ip: str, port : int) -> None:
        self.commandSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.PushSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.killsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.commandSocket.settimeout(2) # 1sec timeout 
        self.sockFile=self.commandSocket.makefile('rw')
        self.pushSockFile=self.PushSocket.makefile('rw')
        self.ip = ip
        self.port = port 
        self.pushPort = port + 1 
        self.killPort = port + 2
     
    def openConnection(self) -> None:
        """
        Open connection to the command socket
        
        :raises TimeoutError: attempted connection but controller did not respond. 
            possible causes, controller is not connected to network or 
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
        self.commandSocket.close()
        return
    
    def openPushConnection(self) -> None:
        """
        Open connection to the push socket
        
        :raises TimeoutError: attempted connection but controller did not respond. 
            possible causes, controller is not connected to network or 
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
        self.PushSocket.close()
        return
    
    def killSocket(self) -> None : 
        """
        method to be used when controller is not responding. 
        this will attempt to connect on the controller ``kill port`` and asks the 
        controller to close all it's open connection. 
        this should act as a soft reset and we will be able to established a new connection 
        with the controller   
    
        :returns: None
        """ 
        try:
            self.killsock.connect((self.ip, self.killPort))
            self.killsock.send("KILL SOCKETS Administrator\r\n".encode())
        except socket.timeout: 
            raise socket.timeout ("\nConnection timeout to IP: "+self.ip + 
                                  " PORT: "+str(self.killPort))
        return
        
    def getID(self) -> str:
        ''' Get the identification string from the controller 
        
        :returns: ethernet controller identification number
        :rtype: str  
        '''
        
        ##TODO: 
        ## aus write and read ein function machen 
    
        self.writeCommand("*IDN?")
        return self.readResponse() 
    
    def getCapabilities(self) -> str:
        '''
        Get the available subcomponents of the ethernet controller like:
            - TR - for controlling transient recorder \r\n
            - APD - for APD remote control \r\n
            - PMT - for PMT remote control \r\n
            - TIMER - for the trigger timing controller \r\n
            - CLOUD - for transient recorder controller cloud mode \r\n
            - BORE  - Boresight alignment system \r\n

        :returns: ethernet controller subcomponents
        :itype: str
        '''
        self.writeCommand("CAP?")
        return self.readResponse() 
    
    def getMilliSecs(self) -> str:
        '''
         Requests the millisecond timer value of the controller 
        
        :returns: millisecond timer value of the controller
        :rtype: str 
        '''
        self.writeCommand("MILLISEC?")
        return self.readResponse() 
        
    def selectTR(self, numTR : int) -> str: 
        """
        select transient recorder to communicate with. 

        :param numTR: transient recorder adresse between 0 .. 7
        :type numTR: int 

        :returns: ``select numTR executed`` or 
            ``Device ID ``numTR` is currently not supported``

        :rtype: str
        """
        if ( not isinstance(numTR, int) ):
            raise ValueError ("selectTR argument must be an integer \r\n" "passed argument is :"+ type(numTR))
        self.writeCommand("SELECT " +str(numTR))
        resp = self.readResponse()
        return resp

    def listInstalledTr(self) -> licel_tr_tcpip.licelTrTCP:
        '''
        Write the number of available Transient recorder in ``MaxTrNumber`` \r\n
        and return a transient recorder object which will be used to communicate with the 
        transient recorder hardware.
        
        :returns: Transient recorder object 
        :rtype: licel_tr_tcpip.licelTrTCP
        '''
        self.selectTR(-1)
        for i in range (0,16): 
            self.selectTR(i)
            self.writeCommand("STAT?")
            resp = self.readResponse()
            if (resp.find("Shots") >= 0):
                self.MaxTrNumber += 1
        if self.MaxTrNumber > 0 :
            return licel_tr_tcpip.licelTrTCP(self.commandSocket,
                                             self.PushSocket,
                                             self.killsock,self.sockFile)
        else:
            print ("no TR detected")
            return 
    
    def _generateMPUSHCommandFromConfig(self, shots, Config, TRHardwareInfos): 
        """
        generate Mpush command from the Configuration ``Config``

        :param shots: number of shots to be acquired currently maximum number of shots supported
            by this python implementation is 256
        :type shots: int

        :param Config: system configuration
        :type Config: Licel.licel_acq.Config()

        :param TRHardwareInfos: list contains hardware information for each detected 
        transient recorder
        :type TRHardwareInfos: dict{Tr_num : dict{'ADC Bits' : ' ', 'PC Bits' : ' ' ,
        FIFOLength': ' ' ,binWidth' : ' ','ID' : ' ', 'HWCAP' : ' ', 'binShift': ' ',
        'raw': ' '}}

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
                    and TRHardwareInfos[trConfig.nTransientRecorder]['ADC Bits'] == 16 ):

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
                    if ((shots > 4096 and TRHardwareInfos[TRnum]['PC Bits'] == 4)
                        or (shots > 1024 and TRHardwareInfos[TRnum]['PC Bits'] == 6)
                        or (shots > 256 and TRHardwareInfos[TRnum]['PC Bits'] == 8)): 
                        
                        tmpCommandPHM = (' {device:2d} {numberToread} PHM {memory}'
                        .format (device = trConfig.nTransientRecorder,
                                numberToread = trConfig.pcBins[key],
                                memory = key)) 
                    command += tmpCommandPC + tmpCommandPHM
        return command   
    
    def MPushStartFromConfig(self, shots :int , Config, TRHardwareInfos):
        '''
        Starts the MPUSH acquisition mode from configuration.
        
        :param shots: number of shots to be acquired currently maximum number of shots supported
            by this python implementation is 256
        :type shots: int

        :param Config: system configuration
        :type Config: Licel.licel_acq.Config()

        :param TRHardwareInfos: list contains hardware information for each detected 
        transient recorder
        :type TRHardwareInfos: dict{Tr_num : dict{'ADC Bits' : ' ', 'PC Bits' : ' ' ,
        FIFOLength': ' ' ,binWidth' : ' ','ID' : ' ', 'HWCAP' : ' ', 'binShift': ' ',
        'raw': ' '}}

        :returns: ethernet controller response 
        :rtype: str 
        '''
        Config.setDatasetsCount(shots, TRHardwareInfos)
        command = self._generateMPUSHCommandFromConfig(shots, Config, TRHardwareInfos) 
        print(command)
        self.writeCommand(command)
        resp = self.readResponse()
        assert resp.find("MPUSH executed") >=0, "\r\nLicel_TCPIP_Licel_TCPIP_MPushStart - Error 5111 : " + resp
        return resp

    def getTrHardwareInfo(self, Tr, Config) -> dict[dict]:
        '''
        get the transient hardware description from each active transient recorder in the 
        configuration.

        :param Tr: transient recorder object 
        :type Tr: licel_tr_tcpip.licelTrTCP

        :param Config: system configuration
        :type Config: Licel.licel_acq.Config()
        
        :returns: a dict containing hardware info for each active transient recorder.
        :rtype: dict{Tr_num : dict{'ADC Bits' : ' ', 'PC Bits' : ' ' , 'FIFOLength': ' ' ,
            binWidth' : ' ','ID' : ' ', 'HWCAP' : ' ', 'binShift': ' ', 'raw': ' '}}
        '''
        hardwareInfo = {}
        for trConfig in Config.TrConfigs:
            transientIsActive = False
            for key in  trConfig.analogueEnabled:
                if (trConfig.analogueEnabled[key] == True  
                    or trConfig.pcEnabled[key]    == True) :
                        transientIsActive = True
            if transientIsActive == True :
                Tr.selectTR(trConfig.nTransientRecorder)
                hardwareInfo[trConfig.nTransientRecorder] = Tr.TRtype()
        return hardwareInfo

    def MPushStop(self, Tr, Config): 
        """ 
        stops the mpush mode for each active transient recorder in config.
        select active transient recorder then sends SLAVE to the controller. 

        :param Tr: transient recorder object 
        :type Tr: licel_tr_tcpip.licelTrTCP

        :param Config: system configuration
        :type Config: Licel.licel_acq.Config()
        
        """
        for trConfig in Config.TrConfigs:
            transientIsActive = False
            for key in  trConfig.analogueEnabled:
                if (trConfig.analogueEnabled[key] == True  
                    or trConfig.pcEnabled[key]    == True) :
                        transientIsActive = True
            if transientIsActive == True :
                Tr.selectTR(trConfig.nTransientRecorder)
                Tr.setSlaveMode()
        return 