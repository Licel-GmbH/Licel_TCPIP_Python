#! python3.10
'''
Copyright ©: Licel Gmbh 
The licelTCP class  Holds methods for handling the sockets with the ethernet controller,
detecting the number of transient recorders present and
starting the MPUSH acquisition from configuration 
'''

import socket
from Licel import licel_tr_tcpip, photomultiplier, TCP_util, licel_SilentStat
import select
import ipaddress

from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from Licel import licel_Config


class EthernetControllerError(Exception):
    """Base exception for EthernetController errors"""
    pass


class EthernetControllerConnectionError(EthernetControllerError):
    """Raised when connection to the controller fails"""
    pass


class EthernetController(TCP_util.util): 

    #: Kill socket command message
    KILL_SOCKETS_CMD: str = "KILL SOCKETS Administrator"
    #: DHCP activated response message
    DHCP_ACTIVATED_RESPONSE: str = "DHCP activated"
    #: Maximum reconnection attempts
    MAX_RECONNECTION_ATTEMPTS: int = 5
    #: Valid port range (1-65535)
    MIN_PORT: int = 1
    MAX_PORT: int = 65535
    #: Command success response
    CMD_EXECUTED_SUCCESS: str = "executed"

    #: Transient Recorder component
    Tr: 'licel_tr_tcpip.TransientRecorder' 
    #: Photomultiplier component
    pmt: 'photomultiplier.photomultiplier'
    #: Silent stat component
    SilentStat: 'licel_SilentStat.SilentStat'
    #: IP address of the controller
    ip: str
    #: Port number for command socket
    port: int
    #: Push buffer for data storage
    pushBuffer: bytearray
  
    def __init__(self, ip: str, port: int) -> None:
        """Initialize the EthernetController.
        
        :param ip: IPv4 address of the controller
        :param port: port number for the command socket
        :raises ValueError: if ip or port are invalid
        """
        self._validate_ip(ip)
        self._validate_port(port)
        self.ip = ip
        self.port = port 
        self._renewSockets()


    def _renewSockets(self) -> None: 
        TCP_util.util.__init__(self, self.ip, self.port)
        self.Tr = licel_tr_tcpip.TransientRecorder(self.commandSocket, self.PushSocket,
                                                   self.killsock, self.sockFile )
        self.pmt = photomultiplier.photomultiplier(self)
        self.SilentStat = licel_SilentStat.SilentStat(self)  

    @staticmethod
    def _validate_ip(ip: str) -> None:
        """Validate IPv4 address format.
        
        :param ip: IP address string to validate
        :raises ValueError: if ip is not a valid IPv4 address
        """
        try:
            ipaddress.IPv4Address(ip)
        except (ipaddress.AddressValueError, ValueError) as e:
            raise ValueError(f"Invalid IPv4 address: {ip}") from e

    @staticmethod
    def _validate_port(port: int) -> None:
        """Validate port number.
        
        :param port: port number to validate
        :raises ValueError: if port is not in valid range (1-65535)
        """
        if not isinstance(port, int) or port < EthernetController.MIN_PORT or port > EthernetController.MAX_PORT:
            raise ValueError(
                f"Invalid port number: {port}. Port must be an integer between "
                f"{EthernetController.MIN_PORT} and {EthernetController.MAX_PORT}")

    @staticmethod
    def _validate_subnet_mask(mask: str) -> None:
        """Validate subnet mask format.
        
        :param mask: subnet mask string to validate
        :raises ValueError: if mask is not a valid IPv4 address
        """
        try:
            ipaddress.IPv4Address(mask)
        except (ipaddress.AddressValueError, ValueError) as e:
            raise ValueError(f"Invalid subnet mask: {mask}") from e

    @staticmethod
    def _validate_password(passwd: str) -> None:
        """Validate password is provided.
        
        :param passwd: password to validate
        :raises ValueError: if passwd is empty or None
        """
        if not passwd:
            raise ValueError("Password must be provided and non-empty")  

    def openConnection(self) -> None:
        """
        Open connection to the command socket
        
        :raises EthernetControllerConnectionError: attempted connection but controller did not respond. 
            Possible causes: controller is not connected to network or 
            controller is already connected to other device
        
        :returns: None
        """
        try:
            self.commandSocket.connect((self.ip, self.port))
        except (socket.timeout, socket.error, OSError) as e:
            raise EthernetControllerConnectionError(
                f"Connection timeout to IP: {self.ip} PORT: {self.port}") from e
        
    def shutdownConnection(self) -> None:
        """
        close connection to the command socket
    
        :returns: None
        """ 
        try:
            self.commandSocket.shutdown(socket.SHUT_RDWR)
        except (socket.error, OSError):
            pass
        finally:
            try:
                self.commandSocket.close()
            except (socket.error, OSError):
                pass
    
    def openPushConnection(self) -> None:
        """
        Open connection to the push socket
        
        :raises EthernetControllerConnectionError: attempted connection but controller did not respond. 
            Possible causes: controller is not connected to network or 
            controller is already connected to other device
        
        :returns: None
        """
        try:
            self.PushSocket.connect((self.ip, self.pushPort))
        except (socket.timeout, socket.error, OSError) as e:
            raise EthernetControllerConnectionError(
                f"Push socket connection timeout to IP: {self.ip} PORT: {self.pushPort}") from e
        
    def shutdownPushConnection(self) -> None: 
        """
        close connection to the push socket
    
        :returns: None
        """ 
        try:
            self.PushSocket.shutdown(socket.SHUT_RDWR)
        except (socket.error, OSError):
            pass
        finally:
            try:
                self.PushSocket.close()
            except (socket.error, OSError):
                pass
    
    def killSocket(self) -> None : 
        """Method to be used when controller is not responding. 
        
        This will attempt to connect on the controller ``kill port`` and asks the 
        controller to close all its open connections. 
        This should act as a soft reset and we will be able to establish a new connection 
        with the controller.

        Used internally in the reconnect mechanisms.

        :raises EthernetControllerConnectionError: if unable to connect to kill port.
        :returns: None
        :rtype: None
        """ 
        try:
            self.killsock.connect((self.ip, self.killPort))
            self.killsock.send((self.KILL_SOCKETS_CMD + "\r\n").encode())
        except (socket.timeout, socket.error, OSError) as e:
            raise EthernetControllerConnectionError(
                f"Kill socket connection timeout to IP: {self.ip} PORT: {self.killPort}") from e
        
    def getID(self) -> str:
        """Get the identification string from the controller.
        
        Queries the controller for its identification information.
        
        :returns: ethernet controller identification number
        :rtype: str
        :raises EthernetControllerConnectionError: if unable to communicate with controller
        """    
        return self._writeReadAndVerify("*IDN?", " ")
    
    def getCapabilities(self) -> str:
        """Get the available subcomponents of the ethernet controller.
        
        Available subcomponents may include:
            - TR - for controlling transient recorder
            - APD - for APD remote control
            - PMT - for PMT remote control
            - PMTSPI - for controller PMT high voltage module via SPI
            - TIMER - for the trigger timing controller
            - CLOUD - for transient recorder controller cloud mode
            - BORE - Boresight alignment system

        :returns: comma-separated list of ethernet controller subcomponents
        :rtype: str
        :raises EthernetControllerConnectionError: if unable to communicate with controller
        """
        return self._writeReadAndVerify("CAP?", "CAP")

    def set_controller_fixed_ip(self, new_ip: str, mask: str, new_port: int, gateway: str, passwd: str) -> Tuple[bool, str]:
        """Send the TCPIP command to the controller to set its network parameters.

        Mirrors the behaviour of the C utility `setfixedipaddress`.

        :param new_ip: new IPv4 address to set on the controller
        :param mask: subnet mask
        :param new_port: port the controller should use after reboot
        :param gateway: default gateway
        :param passwd: current controller password
        
        :returns: tuple of (success, response) where success is True if command executed
        :rtype: Tuple[bool, str]
        
        :raises ValueError: if any parameter is invalid
        """
        # Validate inputs
        self._validate_ip(new_ip)
        self._validate_subnet_mask(mask)
        self._validate_port(new_port)
        self._validate_ip(gateway)
        self._validate_password(passwd)
        
        cmd = f'TCPIP "{new_ip}" "{mask}" "{gateway}" "{new_port}" "{passwd}"'        
        self.writeCommand(cmd)
        resp = self.readResponse()
                   
        if self.CMD_EXECUTED_SUCCESS in resp:
            return True, resp
        return False, resp

    def activate_dhcp(self, nPort: int, passwd: str) -> Tuple[bool, str]:
        """Activate DHCP mode on the controller.

        Sends the command: TCPIP "DHCP" "<nPort>" "<passwd>"
        
        :param nPort: Port number for DHCP
        :param passwd: Controller password
        
        :returns: tuple of (success, response) where success is True if response equals "DHCP activated"
        :rtype: Tuple[bool, str]
        
        :raises ValueError: if passwd is not provided or port is invalid
        """
        self._validate_port(nPort)
        self._validate_password(passwd)
        
        cmd = f'TCPIP "DHCP" "{nPort}" "{passwd}"'
        self.writeCommand(cmd)
        resp = self.readResponse()
        if self.DHCP_ACTIVATED_RESPONSE in resp:
            return True, resp
        return False, resp    
    
    def getMilliSecs(self) -> str:
        """Request the millisecond timer value of the controller.
        
        :returns: millisecond timer value of the controller
        :rtype: str
        :raises EthernetControllerConnectionError: if unable to communicate with controller
        """
        return self._writeReadAndVerify("MILLISEC?", " ")
                     
    def reconnection(self, ConfigInfo: 'licel_Config.Config') -> None:
        """Attempt to reconnect to the controller with automatic retry logic.
        
        Handles socket renewal, connection establishment, and hardware configuration.
        Automatically retries up to MAX_RECONNECTION_ATTEMPTS times on failure.
        
        :param ConfigInfo: Configuration information for hardware setup
        :type ConfigInfo: licel_Config.Config
        :returns: None
        :rtype: None
        :raises EthernetControllerError: if unable to reconnect after maximum attempts
        """
        reconnectAttempt = 0
        self.shutdownConnection()
        self.shutdownPushConnection()
        while reconnectAttempt < self.MAX_RECONNECTION_ATTEMPTS:
            try:
                print(f"Reconnect attempt number {reconnectAttempt}")
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
            except (socket.error, socket.timeout, RuntimeError, Exception,
                    EthernetControllerConnectionError, EthernetControllerError) as e:
                if reconnectAttempt >= self.MAX_RECONNECTION_ATTEMPTS:
                    raise EthernetControllerError(
                        f"Failed to reconnect to {self.ip} after {self.MAX_RECONNECTION_ATTEMPTS} attempts") from e
                else : 
                    print(f"Reconnection attempt {reconnectAttempt} failed: {e}")
                    continue
    



    


    


