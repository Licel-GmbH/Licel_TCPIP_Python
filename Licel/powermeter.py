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
        self.writeCommand("POW CHANNEL "+ str(channel))
        resp= self.readResponse()
        return resp

    def Start(self):
        """
        Activates the data acquisition and data transmission over the push socket.

        :returns: controller response 
        :rtype: str
        """
        self.writeCommand("POW START")
        resp= self.readResponse()
        return resp
    
    def Stop(self):    
        """
        Deactivates the data acquisition and stops the data transmission
        over the push socket

        :returns: controller response 
        :rtype: str
        """
        self.writeCommand("POW STOP")
        resp= self.readResponse()
        return resp
    
    def getTrace(self):
        """
        Starts a single pulse acquisition  \n 
        the single trace is transmitted over the command socket. 

        :returns: and returns one pulse in the following ASCII format: \n 
                  ``<Number of points:N> <Y0> <Y1 >. . . <YN −1 ><CRLF>`` 
        :rtype: str
        """
        self.writeCommand("POW TRACE")
        resp= self.readResponse()
        return resp

    def readPushLine(self):
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
        try:
            # note that sockFile.readline() change \r\n to only \n 
            response = self.pushSockFile.readline()
            if response == '' : 
                raise RuntimeError("socket connection broken",time.localtime())
            else:
                return response
        except socket.timeout: 
            raise RuntimeError( "response timeout",time.localtime())
    