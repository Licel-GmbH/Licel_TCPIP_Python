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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Licel import licel_Config


class EthernetController(TCP_util.util): 


    #:
    Tr: 'licel_tr_tcpip.TransientRecorder' 
    #:
    pmt: 'photomultiplier.photomultiplier'
  
    def __init__(self, ip: str, port : int) -> None:
        self.ip = ip
        self.port = port 
        self._renewSockets()


    def _renewSockets(self) -> None: 
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

    def set_controller_fixed_ip(self, new_ip: str, mask: str, new_port: int, gateway: str, passwd: str) -> tuple[bool, str]:
        """Send the TCPIP command to the controller to set its network parameters.

        Mirrors the behaviour of the C utility `setfixedipaddress`.

        Parameters:
        - new_ip: new IPv4 address to set on the controller
        - mask: subnet mask
        - new_port: port the controller should use after reboot
        - gateway: default gateway
        - passwd: current controller password
        - dry_run: if True, returns the command string instead of sending

        Returns a tuple (success, response_or_command).
        """
        cmd = f'TCPIP "{new_ip}" "{mask}" "{gateway}" "{new_port}" "{passwd}"'        
  
        self.writeCommand(cmd)
        resp = self.readResponse()
                   
        if 'executed' in resp:
            return True, resp
        return False, resp

    def activate_dhcp(self, nPort: int, passwd: str) -> tuple[bool, str]:
        """Activate DHCP mode on the controller.

        Sends the command: TCPIP "DHCP" "<nPort>" "<passwd>"
        Returns (True, response) if response equals "DHCP activated",
        otherwise (False, response).
        """
        if not passwd:
            raise ValueError('passwd must be provided')
        cmd = f'TCPIP "DHCP" "{nPort}" "{passwd}"'
        self.writeCommand(cmd)
        resp = self.readResponse()
        if resp == 'DHCP activated\n':
            return True, resp
        return False, resp    
    
    def getMilliSecs(self) -> str:
        '''
         Requests the millisecond timer value of the controller 
        
        :returns: millisecond timer value of the controller
        :rtype: str 
        '''
        return  self._writeReadAndVerify("MILLISEC?", " ")
                     
    def reconnection(self, ConfigInfo: 'licel_Config.Config') -> None:
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
                self.Tr.listInstalledTr()   
                self.Tr.configureHardware(ConfigInfo)  
                self.pushBuffer = bytearray()
                print("Reconnection Successful")
                break
            except:
                if (reconnectAttempt > MAXRECONNECTIONATTEMPT):
                    raise RuntimeError ("\nFailed to reconnect to "+self.ip+" after 5 attempts") 
                else : 
                    continue
    



    


    


