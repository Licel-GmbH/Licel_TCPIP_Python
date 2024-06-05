
#Copyright ©: Licel Gmbh 

import socket

class util:

    """
    the util class holds utilities method for socket communication. 
    the class is to be inherited by licelTCP and licelTrTCP
    """
    def writeCommand(self,command: str) -> None:
        """
        write the specified command to the ethernet controller. 
        adds <CRLF> to each command before sending.

        :param command: possible command are referenced in \r\n
        https://licel.com/manuals/ethernet_pmt_tr.pdf#page=148

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
    
    def recvPushData(self, pushBuffer : bytearray, BufferSize :int) -> None:
        """
        read push/mpush data from the ethernet controller push port. \r\n
        used for reading push/mpush from transient recorder. \r\n
        fill ``pushBuffer``   

        :param pushBuffer: buffer containing raw binary data \r\n
        :type  pushBuffer: bytearray 

        :param BufferSize: number of byte to be read \r\n 
        :type BufferSize: int
        """
        while len(pushBuffer) < BufferSize:
            packet = self.PushSocket.recv(BufferSize)
            if packet:
                pushBuffer.extend(packet)
                   
        return 