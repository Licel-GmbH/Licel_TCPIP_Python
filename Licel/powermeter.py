from Licel import TCP_util
import socket 
import time 

class powermeter(TCP_util.util):

    run_PushThreads = False
    
    def __init__(self, ethernetController) -> None:
        
        self.commandSocket  = ethernetController.commandSocket
        self.PushSocket     = ethernetController.PushSocket
        self.sockFile       = ethernetController.sockFile
        self.pushSockFile   = ethernetController.pushSockFile

    def selectChannel(self, channel : int):
        """
        Selects the ADC channel for the data acquisition.
         
        :param channel: channel Number can either be 0 for photodiode or 2 for powermeter.
        :type channel: int 
        """
        command = ("POW CHANNEL " + str(channel))
        return self._writeReadAndVerify(command, "executed")


    def Start(self):
        """
        Activates the data acquisition and data transmission over the push socket.

        :returns: controller response 
        :rtype: str
        """
        return self._writeReadAndVerify("POW START", "executed")
    
    def _writeReadAndVerify(self, command, verifystring):
        self.writeCommand(command)
        resp= self.readResponse()
        if resp.find(verifystring) == -1 :
            raise RuntimeError(resp)
        return resp

    def Stop(self):    
        """
        Deactivates the data acquisition and stops the data transmission
        over the push socket

        :returns: controller response 
        :rtype: str
        """
        return self._writeReadAndVerify("POW STOP", "executed")

    
    def getTrace(self):
        """
        Starts a single pulse acquisition.  \n 
        The single trace is transmitted over the command socket. \n
        Push mode must be deactivated. 

        :returns: list of integer representing trace data points: \n 
                  ``[<Y0> <Y1 >. . . <YN  - 1 >]``
        :rtype: list[int]
        """
        resp = self._writeReadAndVerify("POW TRACE", " ")
        resp = resp.replace('\r', '').replace('\n', '')
        splittedResp = resp.split(" ")
        numberOfPointes = splittedResp[0]
        dataPoint = [int(point) for point in  splittedResp[1:]]
        return  dataPoint


    def _readPushLine(self):
        """
        Read push data from the ethernet controller push port. \r\n
        Used for reading push from the powermeter. \r\n
        
        :raises: RuntimeError ``socket connection broken`` if response == None. \n
                 RuntimeError ``response timeout`` when timeout occurs.

        :return: response string containing powermeter data. \n
                 Response have the following format: \n
                 ``<Milliseconds since controller start> <Pulse amplitude ><CRLF>``
        :rtype: str
        """
        return self._readPowermeterPushResponse()
    
    def _readPowermeterPushResponse(self) -> str: 
        """
        low level function, read powermeter push response 

        :raises: RuntimeError if counter part closes the connection, 
                 socketTimeout if counter part does not respond.
        :returns: single line push response is structured as follows: 
            <Milliseconds since controller start> <Pulse amplitude > <triggerNumber> <CRLF>
        :rtype: str
        """
        try:
            # note that sockFile.readline() change \r\n to only \n 
            response = self.pushSockFile.readline()
            if response == '' : 
                raise RuntimeError("socket connection broken")
            else:
                return response
        except socket.timeout: 
            raise socket.timeout( "response timeout")
    
    def _parsePowermeterPushResponse(self, pushResponse) -> list[str , str]:
        """
        parse powermeter single line push response 

        :param: pushResponse: single line push response.
        :type pushResponse: str 

        :returns: list structured as follows: 
            <Milliseconds since controller start> <Pulse amplitude ><triggerNumber>
        :rtype: list[]
        """
        resp_splitted = pushResponse.split(" ")
        timestamp = resp_splitted[0]
        pulseAmplitude = resp_splitted[1].rstrip()   
        if (len(resp_splitted) >= 3 ):
            triggerNumber = resp_splitted[2].rstrip()   
            return timestamp, pulseAmplitude,  triggerNumber
        else : 
            return timestamp, pulseAmplitude, -1

    def getPowermeterPushData(self):
        """
        get powermeter push response

        :returns: list structured as follows: 
            <Milliseconds since controller start> <Pulse amplitude ><triggerNumber>
        :rtype: list[]
        """
        pushDataLine = self._readPushLine()
        timestamp, pulseAmplitude, trigger_num = self._parsePowermeterPushResponse(pushDataLine)
        return timestamp, pulseAmplitude, trigger_num

    def startInternalTrigger(self):
        """
        Activate trigger simulation without waiting for an external trigger.
        
        :raises: RuntimeError if command not executed
        
        :return: controller response
        :rtype: str
        """
        return self._writeReadAndVerify("POWTIMERSIM ON", "executed")  
    
    def stopInternalTrigger(self):
        """
        Deactivate trigger simulation without waiting for an external trigger.
    
        :raises: RuntimeError if command not executed

        :return: controller response
        :rtype: str
        """
        return self._writeReadAndVerify("POWTIMERSIM OFF", "executed")

    def getNumberOfTrigger(self):
        """
        get number of supported number of triggers 

        :raises: RuntimeError if old controller.(command not supported)

        :returns: number of supported trigger
        :rtype: str 
        """
        self.writeCommand("POW NUMTRIG?")
        resp= self.readResponse()
        if resp.find("unknown") != -1:
            raise RuntimeError("POW NUMTRIG? is not supported by old controller.\
                                \r\nController Response: "+resp)
        else: 
            return resp.split(" ")[2]

