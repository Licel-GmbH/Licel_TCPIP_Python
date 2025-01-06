
#Copyright ©: Licel Gmbh

import socket

class util:

    """
    the util class holds utilities method for socket communication. 
    the class is to be inherited by licelTCP and licelTrTCP

    """
    
    def __init__(self, ip: str, port : int):
        self.commandSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.PushSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.killsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.commandSocket.settimeout(2) # 1sec timeout 
        self.PushSocket.settimeout(2)
        self.sockFile=self.commandSocket.makefile('rw')
        self.pushSockFile=self.PushSocket.makefile('rw')
        self.ip = ip
        self.port = port 
        self.pushPort = port + 1 
        self.killPort = port + 2

    def writeCommand(self,command: str) -> None:
        """
        write the specified command to the ethernet controller. 
        adds <CRLF> to each command before sending.

        :param command: possible command are referenced in \r\n
        https://licel.com/manuals/ethernet_pmt_tr.pdf#section.9.1

        :type command: str 
        """
        command = command+"\r\n"
        self.commandSocket.send(command.encode())
        return

    def readResponse(self) -> str:
        """
        read response from the command socket of the ethernet controller. 

        :returns: response string.
        :raises: timeout exception if  fails to respond.
        """
        try:
            # note that sockFile.readline() change \r\n to only \n
            response = self.sockFile.readline()
            return response
        except socket.timeout:
            raise socket.timeout ("Response timeout") 
        
    def recvall(self, nBins) -> bytearray:
        """
        receive the number of nBins specified \r\n

        :param nBins: number of bins to read. Note that a bin consists of uint16, 
                      so the total number of received bytes equals 2* bins    
        :type nBins: int  

        :returns: bytearray of size (2*nBins) containing the raw data.  
        """
        rawData = bytearray()
        while len(rawData) < 2*nBins:
            packet = self.commandSocket.recv(2*nBins - len(rawData))
            if not packet:
                return None
            rawData.extend(packet)
        return rawData
    
    def _writeReadAndVerify(self, command, verifyString):
        """
        helper function to write on the command socket, it reads and verifies the response 

        :param command: command to be sent. 
        :type command: str 

        :param verifyString: substring expected to be received in the response
        :type: str 

        :raises: RuntimeError if the response does not contain the expected `verifyString`

        :returns: response 
        :rtype: str
        """
        self.writeCommand(command)
        resp= self.readResponse()
        if resp.find(verifyString) == -1 :
            raise RuntimeError(resp)
        return resp