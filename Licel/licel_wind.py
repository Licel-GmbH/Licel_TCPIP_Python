from Licel import TCP_util
import struct
import numpy as np

 
# TODO XXX : reqChannelShots is not yet implemented


class Waverider(TCP_util.util):

    setCmd = {  "setShots"    : 1,
                "setFFTsize"  : 2,
                "setNumFFT"   : 3,
    }

    getCmd = {  "reqStart"          :     4, 
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

    possibleFFTSIZE = [32, 64, 128, 256, 512, 1024]

    def __init__(self, ethernetController) -> None:
        
        self.commandSocket  = ethernetController.commandSocket
        self.PushSocket     = ethernetController.PushSocket
        self.sockFile       = ethernetController.sockFile
        self.pushSockFile   = ethernetController.pushSockFile
    
    def _windV2Request(self, command : str)-> str:
        '''
        Low level function for sending and reading requests to/from Wind system
        '''
        rawDataBuffer = bytearray()
        if command not in self.getCmd:
            raise RuntimeError( "command '{command}' is not supported."  
                                 "please see <getCmd> to list support commands"
                                 .format(command = command))
        request = struct.pack('16B', 0, 0, 0, 0, 0, 13, 0, self.getCmd[command],
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

        '''
        if command not in self.setCmd:
            raise RuntimeError("command {command} is not supported."  
                               "please see <setCmd> to list support commands"
                               .format(command = command))
        
        cmd = struct.pack('>8BI', 0, 0, 0, 0, 0, 13, 0, self.setCmd[command],
                          value)
        self.commandSocket.send(cmd)
        bytesToRead = self.__getBytesToRead__()
        resp = self.commandSocket.recv(bytesToRead)
        return resp.decode("utf-8")
    
    def __swap_endian_32bit__(self, num):
        '''
        helper function that return the given number as little endian.
        '''
        return int.from_bytes(num.to_bytes(4, byteorder='big'), byteorder='little')

    def __getBytesToRead__(self, ) -> int:
        '''
        helper function that flushes the socket buffer and 
        returns the expected bytes to be read.
        '''
        self.commandSocket.recv(8) # read out first 8 Byte from TCP protocol Header
        bytesToRead = self.commandSocket.recv(4)
        return struct.unpack('>I', bytesToRead)[0]
    
    def setFFTsize(self, fftSize: int) -> str:
        '''
        set the FFT size. 
        possible fftSize values are : 64, 128, 256
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
        TODO: XXXXX fftNum: MIN - MAX undocumented. it is to mean 
        '''
        return self._windV2Set("setNumFFT",fftNum)
    
    def setShots(self, shots: int) -> str:
        '''
        Sets the number of shots to be averaged for one run
        return string response from the ethernet controller
        '''
        return self._windV2Set("setShots",shots)
    
    def getShotsSettings(self) -> str:
        '''
        get the shots that are to be acquired for one run. 
        return string response from the ethernet controller
        '''
        return self._windV2Request("reqShots")

    def getCurrentShots(self)->int:
        '''
        get the shots that are were currently acquired. 
        return int correspanding to the current shots acquired by the waverider.
        '''
        return int (self._windV2Request("reqCurrShots").split(": ")[1])

    def getFFTsize(self) -> str:
        '''
        return the FFT size. 
        possible return values are : 64, 128, 256
        '''
        return self._windV2Request("reqFFTsize")
         
    def getNumFFT(self) -> str: 
        '''
        get the number of FFT to be computed after each trigger event.
        '''
        return self._windV2Request("reqNumFFT")
    
    def getID(self) -> str: 
        
        return self._windV2Request("reqIDN")  

    def getCAP(self) -> str:
        return self._windV2Request("reqCAP")  

    def getHWDescr(self) -> str:
        return self._windV2Request("reqHWDESC") 
    
    def getMSEC(self) -> int:
        return int (self._windV2Request("reqMSEC").split(": ")[1])  

    def startAcq(self) -> str:
        return self._windV2Request("reqStart")  

    def isDataAvailable(self) -> bool:

        if  self._windV2Request("reqDataAvailable") != 0:
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
        '''
        return self._windV2Request("reqData")

    def getData(self, FFT_Size, numFFT) -> list[np.ndarray[np.uint64], 
                                                np.ndarray[np.uint64]]:
        
        '''
        get the data from the wave rider via tcp/ip socket.
        this function will send a data request command to the waverider, 
        upon reciveing the expected number of byte, we extract the timestamp and 
        the data array from the socket buffer and remove the delimiter padding. 

        the DC part of the FFT will also be overwritten with the next 
        meanungful fft value.
        '''
        raw_data = self.getRawData()
        del raw_data[0:4] #delete payload size padding
        dt = np.dtype(np.uint64)
        dt = dt.newbyteorder('<')

        timeStamp = np.frombuffer(raw_data[0:8], dtype=np.dtype(np.uint64))
        del raw_data[0:8] #remove timestamp from fft raw data
        del raw_data[0:8] #remove 0x00000 padding  from fft raw data

        data = np.frombuffer(raw_data, dtype=dt)
        
        ##remove delimiter from data.
        i = 0
        for i in range(0 , int (len(data)/(FFT_Size/2))):
            index = int (i*FFT_Size/2)
            data[index] = data[index+1]
        # The raw data size is be 128K, and it will be dumped by the waverider into our socket.
        # the computed Powerspectrum (useful data) goes from index 0 ...(FFT_Size*numFFT/2)
        # the rest of the data is fillied with zero. 
        # here we remove the zeros. 
        powerSpectrum = np.delete(data, np.s_[int(FFT_Size*numFFT/2):data.size],None)
        return timeStamp, powerSpectrum

    def calcLidarRangeResolution(self, samplingRate_hz : int, fftsize : int) -> float:
        '''
        return lidar range resolution in meters. 
        
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
        '''
        samplingPeriode_us = (1/sampleRate_HZ) * 1000000
        return fftsize * samplingPeriode_us
    
    def getRangebins(self, distance: int, fftSize: int, samplingRate_hz:int) -> str:
        '''
        return the number of fft that needs to be computed, to acquire data up until 
        the specified range. 

        '''
        if distance > 39320:
            raise RuntimeError ("Maximal Tracelength is 39320 meters \r\n")
        lidarRangeResolution = self.calcLidarRangeResolution(samplingRate_hz, fftSize)
        return int(distance / lidarRangeResolution) 

    def calcFrequencyIncrement(self, SamplingRate_HZ : int, FFTsize : int) -> float:
        '''
        return the  spectral resolution of the measurment.
        '''
        return SamplingRate_HZ / FFTsize
    
