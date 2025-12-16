from Licel import TCP_util, licel_data
import numpy as np
import os
from typing import  Any
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from Licel import  licel_SP32_Config, licel_tcpip
from datetime import datetime
class SP32(TCP_util.util):

    __WideMEM = False
    __Rangebins = 4000 
    
    
    def __init__(self, ethernetController: 'licel_tcpip.EthernetController') -> None:
        self.commandSocket = ethernetController.commandSocket 
        self.sockFile      = ethernetController.sockFile

    def getHardwareID(self) -> str:
        """
        get hardware ID of the SP32 controller 

        :returns: controller hardware ID and setting. the response is 
        structured as follows: 
        
            HW: HWREV BINLEN MAXRANGEBINS BINSIZE MAXSHOTS ENDIANNESS
            PUSH: MAXPUSHSHOTS CMPFACTOR VARCOMP VARTRACE CURRENTRANGEBINS
            MAXBINLEN HIGHRES: MINBINLEN MINRANGEBINS WIDEMEM
        
        :rtype: str
        """
        command = "HW?"
        resp = self._writeReadAndVerify(command, "HW")
        return resp
    
    def getCapabilites(self) -> str:
        """
        get capabilities of the SP32 controller 

        :returns: controller capabilities. 

        :rtype: str
        """
        command = "CAP?"
        resp = self._writeReadAndVerify(command, "CAP")
        if resp.find("32CHANNEL") == -1 :
            print(resp)
            raise RuntimeError("returned capabilities do not indicate SP32") 
        return resp 
    
    def getCurrent(self) -> str:
        """
        get current settings of the SP32 controller 
        Explicitely return the ADC value of the on 
        board high voltage supply current sensor 
        
        :returns: controller current settings. 

        :rtype: str
        """
        command = "CURRENT?"
        resp = self._writeReadAndVerify(command, "Current")
        return resp

    def getDieTemperature(self) -> str:
        """
        get die temperature of the SP32 controller 
        
        :returns: controller die temperature in degree Celsius.

        :rtype: str
        """
        command = "DIETEMP?"
        resp = self._writeReadAndVerify(command, "DIETEMP")
        return resp
    
    def getPCBTemperature(self) -> str:
        """
        get the PCB board temperature of the SP32 controller 
        
        :returns: controller PCB board temperature in degree Celsius.

        :rtype: str
        """
        command = "TEMP?"
        resp = self._writeReadAndVerify(command, "Temperature")
        return resp
    
    def setDiscriminator(self, disc: int) -> str:
        """
        Sets the discriminator level of the detector.
        Valid values for the discriminator are 0–63
        
        :param disc: discriminator level (0-63)
        :type disc: int

        :returns: controller response
        :rtype: strs
        """
        if disc < 0 or disc > 63:
            raise ValueError("Discriminator level must be between 0 and 63")
        command = f"DISCRIMINATOR {disc}"
        resp = self._writeReadAndVerify(command, "DISCRIMINATOR")
        return resp
    
    def getHV(self) -> str:
        """
        get Voltage of the pmt 

        :returns: controller response containing the pmt high voltage 
        :rtype: str
        """

        command = ("PMT? 0")
        self.writeCommand(command)
        resp= self.readResponse()
        return resp
    
    def setHV(self, Voltage:int) ->str:
        """
        set voltage for the pmt 

        :param voltage: desired pmt voltage in Volt
        :type voltage: int

        :returns: controller response 
        :rtype: str
        """
        command = ("PMTG 0 {voltage:4d}"
                   .format(voltage = Voltage))
        self.writeCommand(command)
        resp= self.readResponse()
        return resp
    
    def enablePretrigger(self) -> str:
        '''
        Enable the pretrigger for a 
        '''
        return  self._writeReadAndVerify("PRETRIG 1", "executed")
    
    def disablePretrigger(self) -> str:
        ''' Disable the pretrigger '''
        return  self._writeReadAndVerify("PRETRIG 0", "executed")
    
    def setTimeResoultion(self, Resolution :float) -> str:
        """
        set the resolution at which the detector must acquire the data. 
        supported High resolution modes are multiple of 0.625ns up until 10ns.
        supported standard resolution modes are multiple of 10ns up until 10000ns.

        :param Resolution: desired detector timing resolution
        :type Resolution: float

        :returns: controller response 
        :rtype: str
        """
        if Resolution > 200 :
            self.WideMemON()
        else:
            self.WideMemOFF()
            
        command = ("RESOLUTION {Resolution:10.4f}"
                   .format(Resolution = Resolution))
        resp = self._writeReadAndVerify(command, "executed")
        return resp        
    
    def setRange(self, Rangebins: int) -> str: 
        """
        set the number of rangebins the detector must acquire 

        :param Rangebins: desired Range
        :type Rangebins: int

        :returns: controller response 
        :rtype: str
        """
        command = ("RANGEBINS  {Rangebins:5d}"
                   .format(Rangebins = Rangebins))
        self.writeCommand(command)
        resp= self.readResponse()
        return resp       
    
    def openShutter(self) -> str: 
        """
        Opens  the mechanical shutter of the spectrometer.
        This command is available as an option.

        :returns: controller response 
        :rtype: str
        """
        command = ("SHUTTER OPEN")
        self.writeCommand(command)
        resp= self.readResponse()
        return resp 
    
    def closeShutter(self) -> str: 
        """
        Close the mechanical shutter of the spectrometer.
        This command is available as an option.

        :returns: controller response 
        :rtype: str
        """
        command = ("SHUTTER CLOSED")
        self.writeCommand(command)
        resp= self.readResponse()
        return resp 
    
    def getShutterPosition(self) -> str: 
        #XXX TODO: verify this command in hardware.
        """
        Requst the current position of the mechanical shutter. 
        This command is available as an option.

        :returns: controller response 
        :rtype: str
        """
        command = ("SHUTTER?")
        self.writeCommand(command)
        resp= self.readResponse()
        return resp 
    
    def startInternalTrigger(self) -> str:

        """
        Sets the trigger mode to internal 

        :returns: controller response 
        :rtype: str
        """
        command = ("SIM ON")
        self.writeCommand(command)
        resp= self.readResponse()
        return resp 
    
    def stopInternalTrigger(self) -> str:

        """
        Sets the trigger mode to external 

        :returns: controller response 
        :rtype: str
        """
        command = ("SIM OFF")
        self.writeCommand(command)
        resp= self.readResponse()
        return resp 
    
    def stopAcquisition(self) -> str:
        """
        Stops the data acquisition of the detector

        :returns: controller response 
        :rtype: str
        """
        command = ("STOP")
        self.writeCommand(command)
        resp= self.readResponse()
        return resp 
    
    def getStatus(self) -> tuple[str, int, int, float, float]: 
        """
        Returns the current status of the controller. The format of the reply is :
        RUN: AcqStatus, ShotNum Shots of TargetShotNum Current Timestamp

        - AcqStatus is the acquisition status of the detector, which can be either 0 (Idle),1 (Armed), or 2 (Acquiring).
        - ShotNum is the current shots acquired.
        - TargetShotNum is the target shots to acquire set by the START command.
        - Current is the ADC value of the on board high voltage supply current sensor.
        - Timestamp in milliseconds (accurate to micro seconds) since powering on the controller.

        An example reply would be:
        Run: 2, 10 Shots of 100 65535 9070.000000

        :returns: controller response 
        :rtype: str
        """
        command = ("STAT?")
        self.writeCommand(command)
        resp= self.readResponse()
        state = resp.split(" ")[1]
        if state == "0,":
            state_str = "Idle"
        elif state == "1,":
            state_str = "Armed"
        elif state == "2,":
            state_str = "Acquiring"
        else:
            state_str = "Unknown"
        shots = resp.split(" ")[2]
        targetshots = resp.split(" ")[5]
        current = int(resp.split(" ")[6]) * 0.0008 
        timestamp = float(resp.split(" ")[7].strip('\n').replace(',','.'))
        return state_str, int(shots), int(targetshots), float(current), timestamp
    
    def WideMemON(self) -> str:
        self.__WideMEM = True
        command = ("WIDEMEM 1")
        self.writeCommand(command)
        resp= self.readResponse()
        return resp 
    
    def WideMemOFF(self) -> str:
        self.__WideMEM = False
        command = ("WIDEMEM 0")
        self.writeCommand(command)
        resp= self.readResponse()
        return resp 

    def startAcquisition(self, shots: int) -> str:
        """
        Starts the data acquisition of the detector

        :param shots: number of shots to acquire
        :type shots: int

        :returns: controller response 
        :rtype: str
        """
        command = ("START {shots:10d}"
                   .format(shots = shots))
        try:
            resp = self._writeReadAndVerify(command, "executed")   
        except Exception as e:   
            if str(e).find("Turn on Wide Memory Mode!") >= 0:
                self.WideMemON()
                resp = self._writeReadAndVerify(command, "executed")   
            else:
                raise e
        return resp

    def getData(self) -> tuple [int, np.ndarray[Any, np.dtype[np.uint32]]]:
       """
       get acquired data from the SP32 controller 
    
       :returns: acquired data from the controller 
       :rtype: str
       """
       # always turn off wide memory before data readout
       command = "DATA?"
       self.writeCommand(command)
       shots, traces, bins = self.__readHeader()
       if self.__WideMEM == True:
           data : np.ndarray[Any, np.dtype[np.uint32]] = np.zeros((traces, bins), dtype=np.uint32)  
           data_bytes = self.recvall(2*traces*bins)
           data = np.frombuffer(data_bytes, dtype='<u4')
       else:
           data_bytes = self.recvall(traces*bins)
           data = np.frombuffer(data_bytes, dtype='<u2')
           data = data.astype(np.uint32)
       shapedData = data.reshape((traces, bins))
       return shots, shapedData




    def __readHeader(self) -> tuple[int, int, int]:
        """
        read data header from the SP32 controller 

        :returns: data header from the controller 
        :rtype: str
        """
        Marker = self.recvall(2)
        shots  = self.recvall(2)
        traces = self.recvall(2)
        bins   = self.recvall(2)

        shots_int  =  int.from_bytes(shots, byteorder='little', signed=False)
        traces_int =  int.from_bytes(traces, byteorder='little', signed=False)
        bins_int   =  int.from_bytes(bins, byteorder='little', signed=False)
        return shots_int, traces_int, bins_int  


    def saveSP32Data(self, Config: 'licel_SP32_Config.SP32_Config', starttime: datetime,
                     stoptime: datetime, prefix: str, shots: int,
                     data: np.ndarray[Any, np.dtype[np.uint32]]) -> None:
        """
        save acquired data to a licel file format 

        :param filename: name of the file to save the data
        :type filename: str

        :param data: acquired data from the controller 
        :type data: np.ndarray[Any, np.dtype[np.uint32]]

        :returns: None
        :rtype: None
        """
        
        dataHandler = licel_data.DataParser()
        Config.numDataSets = 32
        filename = dataHandler._generateFileName(prefix)

        fileDescriptor = open (os.path.join(Config.measurmentInfo.szOutPath,filename), 'ab')
        my_startTime = starttime.strftime("%d/%m/%Y %H:%M:%S")
        my_stopTime = stoptime.strftime("%d/%m/%Y %H:%M:%S")
        
        secondHeader = dataHandler._generateSecondHeaderline(Config,my_startTime,my_stopTime)
        thirdHeader = dataHandler._generateThirdHeaderline(Config, shots, 10)

        fileDescriptor.write("{filename}\n".format(filename=filename).encode())
        fileDescriptor.write(secondHeader.encode())
        fileDescriptor.write(thirdHeader.encode())
        fileDescriptor.write(self.__generateSP32Headerline(Config.SP32param.noBins,
                                                           Config.SP32param.HV,
                                                           Config.SP32param.binwidth_ns,
                                                           Config.SP32param.centralWavelength,
                                                           Config.SP32param.nm_PerChannel,
                                                           shots, 
                                                           Config.SP32param.discriminator)
                                                           .encode())
        fileDescriptor.write(b'\n')

        for i in range (Config.numDataSets):
            fileDescriptor.write(data[i][0:Config.SP32param.noBins])
            fileDescriptor.write(b'\r\n')
        fileDescriptor.close()

        return
    
    def __generateSP32Headerline(self, bins:int, pmtHV:int, binwidth: float,
                                 centralWavelength:float, nm_PerChannel:float,
                                 shots:int, discriminator:int) -> str:
        myHeaderLine = ""
        rangeResolution = binwidth *150 / 1000 # convert bindth from ns to meters
        startwavelength = centralWavelength + (15.5 * nm_PerChannel)
        SCALING_FACTOR = 25/63  # from labview 

        for i in range (32):
            wavelength = startwavelength - i * nm_PerChannel
            header =(" 1 1 1 {dataPoints} 1 {pmtHV:04d}"
                     " {binwidth:1.2f} {wavelength:4.2f} {polStatus} 0"
                     " {binshift:02d} {binshift_dec:3d} {adc:02d}"
                     " {shots:06d} {myRange:6.4f} BC{Channel:02X}\n"
                                .format(dataPoints = bins,
                                    pmtHV = pmtHV,
                                    binwidth = float(rangeResolution),
                                    wavelength = float (wavelength),
                                    polStatus = 0,
                                    binshift = int(0), 
                                    binshift_dec = int (0), 
                                    adc = 0, 
                                    shots = shots, 
                                    myRange = discriminator * SCALING_FACTOR,
                                    Channel = i))
            myHeaderLine += header
        return myHeaderLine

