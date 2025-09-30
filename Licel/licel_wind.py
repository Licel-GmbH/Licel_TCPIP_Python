from Licel import TCP_util
import struct
import numpy as np

 
# TODO XXX : reqChannelShots is not yet implemented


class Waverider(TCP_util.util):

    #: map the setter commands with their low level value.
    setterCommands = {  "setShots"    : 1,
                        "setFFTsize"  : 2,
                        "setNumFFT"   : 3,
    }

    #: map the getter commands with their low level value.
    getterCommands = {  "reqStart"          :     4, 
                        "reqDataAvailable"  :     5, 
                        "reqShots"          :     6, 
                        "reqCurrShots"      :     9, 
                        "reqData"           :    12,
                        "reqIDN"            :    13,
                        "reqMSEC"           :    14,
                        "reqMAC"            :    15,
                        "reqHWDESC"         :    21,
                        "reqCAP"            :    22,
                        #"reqChannelShots"   :    23,
                        "reqNumFFT"         :    24,
                        "reqFFTsize"        :    25,
    }

    #: list the allowed value for the fft size
    possibleFFTSIZE = [32, 64, 128, 256, 512, 1024]

    def __init__(self, ethernetController) -> None:
        
        self.commandSocket  = ethernetController.commandSocket
        self.PushSocket     = ethernetController.PushSocket
        self.sockFile       = ethernetController.sockFile
        self.pushSockFile   = ethernetController.pushSockFile
    
    def _windV2Request(self, command : str)-> str:
        '''
        Low level function for sending and reading requests to/from Wind system.
        
        :param command: the command to be sent to the waverider. 
        :type command: str, defined in the ``getterCommands``. 

        :return: waverider response. should contain ``executed`` if successful.
        :rtype: default is str. only the command ``getDATA`` returns byte array.
        '''
        rawDataBuffer = bytearray()
        if command not in self.getterCommands:
            raise RuntimeError( "command '{command}' is not supported."  
                                 "please see <getterCommands> to list support commands"
                                 .format(command = command))
        request = struct.pack('16B', 0, 0, 0, 0, 0, 13, 0, self.getterCommands[command],
                            0, 0, 0, 0, 0, 0, 0, 0)
        self.commandSocket.send(request)
        bytesToRead = self.__getBytesToRead__()
        
        if command  == "reqDataAvailable":
            return bytesToRead
        
        if command == "reqData":
            while len(rawDataBuffer) != self.__swap_endian_32bit__(bytesToRead):
                packet = self.commandSocket.recv(self.__swap_endian_32bit__(bytesToRead))
                if packet:
                    rawDataBuffer.extend(packet)
            # we return the raw binary data.
            return rawDataBuffer
        
        resp = self.commandSocket.recv(bytesToRead)
        try:
            return (resp.decode("utf-8"))
        except:
            return (str(int.from_bytes(resp, 'big')))

    def _windV2Set(self, command, value) -> str:
        '''
        Low level function for setting and reading parameters to/from Wind system
        will
        :param command: the commands defined in `setterCommands`.
        :type command: str

        :param value: value to be set. 
        :type value: int

        :return: waverider response. should contain “executed” if successful.
        :rtype: str.
        '''
        if command not in self.setterCommands:
            raise RuntimeError("command {command} is not supported."  
                               "please see <setterCommands> to list support commands"
                               .format(command = command))
        
        cmd = struct.pack('>8BI', 0, 0, 0, 0, 0, 13, 0, self.setterCommands[command],
                          value)
        self.commandSocket.send(cmd)
        bytesToRead = self.__getBytesToRead__()
        resp = self.commandSocket.recv(bytesToRead)
        return resp.decode("utf-8")
    
    def __swap_endian_32bit__(self, num):
        '''
        helper function that return the given number as little endian.

        :param num: value to be swapped. 
        :type num: bytearray

        :return: value with swapped endianness.
        :rtype: int 
        '''
        return int.from_bytes(num.to_bytes(4, byteorder='big'), byteorder='little')

    def __getBytesToRead__(self) -> int:
        '''
        helper function that flushes the socket buffer and 
        returns the expected bytes to be read.

        :return: number of byte to be read from the socket.
        :rtype: int
        '''
        self.commandSocket.recv(8) # read out first 8 Byte from TCP protocol Header
        bytesToRead = self.commandSocket.recv(4)
        return struct.unpack('>I', bytesToRead)[0]
    
    def setFFTsize(self, fftSize: int) -> str:
        '''
        set the FFT size.

        :param fftSize: number of ADC samples that goes into computing one fft.
                        should a power of 2 between 32 and 1024.
        :type fftSize: int

        :return: ethernet controller response, should be ``FFTSIZE executed``
        '''

        if fftSize not in self.possibleFFTSIZE: 
            raise RuntimeError ("unexpected fftSize value. Possible value are: \r\n", \
                                 self.possibleFFTSIZE)
        cmd = "FFTSIZE " +str (fftSize)
        resp = self._windV2Set("setFFTsize",fftSize)
        return resp

    def setNumFFT(self, fftNum: int) -> str:
        '''
        Sets the number of FFT to be computed after each trigger event.

        :param fftNum: number of fft to be computed.
        :type fftNum: int

        :return:  response from the ethernet controller, 
        should be NUMFFT <nFFT> executed.
        :rtype: str
        '''
        return self._windV2Set("setNumFFT",fftNum)
    
    def setShots(self, shots: int) -> str:
        '''
        Sets the number of shots to be averaged for one run

        :param shots: Number of shots to be collected in a single collection.
        :type shots: int

        :return: response from the ethernet controller, 
        should be: `SHOTS <nShots> executed`
        :rtype: str
        '''
        return self._windV2Set("setShots",shots)
    
    def getShotsSettings(self) -> str:
        '''
        get the shots that are to be acquired for one acquisition.

        :return: number of shots that are to be acquired.
        :rtype: str
        '''
        return self._windV2Request("reqShots")

    def getCurrentShots(self)->int:
        '''
        get the shots that are currently acquired.

        :return: corresponding to the current shots acquired by the waverider.
        :rtype: int
        '''
        return int (self._windV2Request("reqCurrShots").split(": ")[1])

    def getFFTsize(self) -> str:
        '''
        get the FFT size. the fft size represents the number of ADC samples 
        that goes into computing a single FFT. 
        FFT size must be set by the user before starting the acquisition. 

        :return: FFT size, typically a power of 2 between 32 and 1024. 
        :rtype: str
        '''
        return self._windV2Request("reqFFTsize")
         
    def getNumFFT(self) -> str: 
        '''
        get the number of FFT to be computed after each trigger event.

        :return: number of fft to be computed.
        :rtype: str
        '''
        return self._windV2Request("reqNumFFT")
    
    def getID(self) -> str: 
        '''
        Query the waverider for it's identification number. 

        :return: Firmware revision date, for example `Wind_v2_15.11.2024 `
        :rtype: str
        '''
        return self._windV2Request("reqIDN")  

    def getCAP(self) -> str:
        '''
        Query the hardware for it's capability. 

        :return: the waverider should return `CAP: Wind `
        :rtype: str
        '''
        return self._windV2Request("reqCAP")  

    def getHWDescr(self) -> str:
        '''
        get the Hardware revision.

        :return: waverider response containing hardware revision.
        :rtype: str
        '''
        return self._windV2Request("reqHWDESC") 
    
    def getMSEC(self) -> int:
        '''
        get waverider time since boot in milliseconds. 

        :return: waverider time since boot in milliseconds.
        :rtype: int.
        '''
        return int (self._windV2Request("reqMSEC").split(": ")[1])  

    def startAcq(self) -> str:
        '''
        start the waverider acquisition. 

        :return: waverider response, returns ``START executed`` upon success. 
        :rtype: str 
        '''
        return self._windV2Request("reqStart")  

    def isDataAvailable(self) -> bool:
        '''
        Query the waverider for data availability. 

        :return: True if data is available.
        :rtype bool:
        '''
        ret = self._windV2Request("reqDataAvailable")
        if ret  != 0:
            return True  
        else :
            return False
    
    def getRawData(self) -> bytearray:
        '''
        The wind will return the following data package: 
        | 8 bytes Header 0x00 00 00 D0 00 0C 00 00 | 
        | 4 bytes Payload Size +  4 Bytes padding  | 
        | 8 Bytes Time stamp    | 
        | 8 bytes 0x00 zero padding                |
        | Payload     2^15  bytes                  |

        The header and the 4 bytes payload size will be "consumed" by windV2Request
        all we are left with is 
        (4 bytes payload size padding +
         4 bytes timestamp            +
         4 bytes padding              +
         8 bytes zero padding         +
        actual payload (8*2^15)         ). 
        4 + 8 + 8 + 8 * 2^15 = 262164 Bytes

        :return: raw power spectra data.
        :rtype: byte array.
        '''

        return self._windV2Request("reqData")

    def getData(self, FFT_Size, numFFT) -> list[np.ndarray[np.uint64], 
                                                np.ndarray[np.uint64]]:
        
        '''
        The data is retrieved from the Wave Rider via a TCP/IP socket.
        This function sends a data request command to the Wave Rider. 
        After receiving the expected number of bytes, we extract the timestamp and 
        the data array from the socket buffer and remove the separator padding. 

        The DC part of the FFT is also overwritten with the next 
        meaningful FFT value.

        :param FFT_Size: the number of ADC sample that goes into computing a single FFT
        :type FFT_Size: int

        :param numFFT: number of fft to be computed.
        :type numFFT: int

        :return: The waverider timestamp in milliseconds, and the power spectra data.
                 note that the timestamp correspond to when the data request
                 is received by the waverider.
        :rtype: list[np.ndarray[np.uint64], np.ndarray[np.uint64]]  
        '''
        raw_data = self.getRawData()
        del raw_data[0:4] #delete payload size padding
        dt = np.dtype(np.uint64)
        dt = dt.newbyteorder('<')

        timeStamp = np.frombuffer(raw_data[0:8], dtype=np.dtype(np.uint64))
        del raw_data[0:8] #remove timestamp from fft raw data
        del raw_data[0:8] #remove 0x00000 padding  from fft raw data

        data = np.frombuffer(raw_data, dtype=dt)
        
        ##remove the DC part from data.
        i = 0
        for i in range(0 , int (len(data)/(FFT_Size/2))):
            index = int (i*FFT_Size/2)
            data[index] = data[index+1]
        # The raw data size is 128K, and it will be dumped by the waverider into our socket.
        # the computed Powerspectrum (useful data) goes from index 0 ...(FFT_Size*numFFT/2)
        # the rest of the data is fillied with zero. 
        # here we remove the zeros. 
        powerSpectrum = np.delete(data, np.s_[int(FFT_Size*numFFT/2):data.size],None)
        return timeStamp, powerSpectrum

    def calcLidarRangeResolution(self, samplingRate_hz : int, fftsize : int) -> float:
        '''
        return lidar range resolution in meters. 

        :param samplingRate_hz: the waverider ADC sampling rate in hertz.
        :type samplingRate_hz: int.

        :param fftsize: the number of ADC sample that goes into computing a single FFT
        :type fftsize: int

        :return: the Lidar range resolution in meters
        :rtype: int.
        
        '''
        light_spped_m_us = 300 # 300m is the distance travelled by light in 1 micro-second. 
        timeResolution_us = self.calcTimeResolution(samplingRate_hz,fftsize)
        return timeResolution_us * light_spped_m_us/2
    
    def calcTimeResolution(self, sampleRate_HZ : int, fftsize : int) -> float:
        '''
        return the time resolution of one FFT bin in micro seconds.

        the time resolution depend on the number of sample that goes into
        computing a single fft and the sample rate of the device. 

        for example a device with 250MHZ sample rate acquire a sample each  4ns 
        let's assume that we feed 128 samples into a single fft. the calculated
        time resolution will than be 4ns * 128 =  512ns

        :param samplingRate_hz: the waverider ADC sampling rate in hertz.
        :type samplingRate_hz: int.

        :param fftsize: the number of ADC sample that goes into computing a single FFT
        :type fftsize: int

        :return: the time resoulution in us
        :rtype: int.
        '''
        samplingPeriode_us = (1/sampleRate_HZ) * 1000000
        return fftsize * samplingPeriode_us
    
    def getRangebins(self, distance: int, fftSize: int, samplingRate_hz:int) -> str:
        '''
        return the number of fft that needs to be computed, to acquire data up until 
        the specified range. 

        :param distance: the maximal distance range we want to acquire in meters
        :type distance: 

        :param samplingRate_hz: the waverider ADC sampling rate in hertz.
        :type samplingRate_hz: int.

        :param fftsize: the number of ADC sample that goes into computing a single FFT
        :type fftsize: int

        :return: rounded down number of fft to be computed.
        :rtype: int.
        '''
        if distance > 39320:
            raise RuntimeError ("Maximal Tracelength is 39320 meters \r\n")
        lidarRangeResolution = self.calcLidarRangeResolution(samplingRate_hz, fftSize)
        return int(distance / lidarRangeResolution) 

    def calcFrequencyIncrement(self, SamplingRate_HZ : int, fftsize : int) -> float:
        '''
        return the spectral resolution of the measurement.

        :param samplingRate_hz: the waverider ADC sampling rate in hertz.
        :type samplingRate_hz: int.

        :param fftsize: the number of ADC sample that goes into computing a single FFT
        :type fftsize: int
        '''
        return SamplingRate_HZ / fftsize
    
