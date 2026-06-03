from Licel import TCP_util
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from Licel import licel_tcpip


class SilentStat(TCP_util.util):



    def __init__(self, ethernetController: 'licel_tcpip.EthernetController') -> None:
        
        self.commandSocket = ethernetController.commandSocket 
        self.sockFile      = ethernetController.sockFile
    
    def getState(self) -> str:
        """
        Get the current state of the silent stat. \n 
        Returns the raw controller response string.

        :returns: controller response
        :rtype: str
        """
        
        return self._writeReadAndVerifyFeatureSupport("SILENCESTAT?", "SILENCESTAT is")
    
    def ON(self) -> str:
        """
        Activate the silent stat. \n
        In this state, the controller will delay the STAT? command sent to the
        selected transient recorder for the specified delay times around every
        trigger. All other commands are still forwarded instantaneously.

        :returns: controller response
        :rtype: str
        """
        return self._writeReadAndVerifyFeatureSupport("SILENCESTAT ON", "SILENCESTAT ON executed")

    def OFF(self) -> str:
        """
        Deactivate the silent stat. \n
        In this state, the controller will not delay the STAT? command sent to the
        selected transient recorder.

        :returns: controller response
        :rtype: str
        """
        return self._writeReadAndVerifyFeatureSupport("SILENCESTAT OFF", "SILENCESTAT OFF executed")

    def setDelay(self, preTriggerBlock_us: int, postTriggerBlock_us: int) -> str:   
        """
        Set the pre-trigger and post-trigger block delay times for the silent stat. \n
        The delay times are specified in microseconds. \n
        The controller will delay the STAT? command sent to the selected transient
        recorder for the specified delay times around every trigger when the silent
        stat is activated. All other commands are still forwarded instantaneously.

        :param preTriggerBlock_us: pre-trigger block delay time in microseconds
        :type preTriggerBlock_us: int
        :param postTriggerBlock_us: post-trigger block delay time in microseconds
        :type postTriggerBlock_us: int
        :returns: controller response
        :rtype: str
        """

        # The command format is: "SILENCESTAT DELAY <postTriggerBlock_us> <preTriggerBlock_us>"
        command = f"SILENCESTAT DELAY {postTriggerBlock_us} {preTriggerBlock_us}"
        return self._writeReadAndVerifyFeatureSupport(command, "executed")
           
    def getDelay(self) -> Tuple[float, float]:
        """
        Get the current pre-trigger and post-trigger block delay times for the silent stat. \n 
        The delay times are returned in microseconds.

        :returns: tuple containing pre-trigger and post-trigger block delay times in microseconds
        :rtype: Tuple[float, float]
        """
        response = self._writeReadAndVerifyFeatureSupport("SILENCESTAT DELAY?", "SILENCESTAT DELAY after:")
        parts = response.split()
        postTriggerBlock_us = float(parts[3])
        preTriggerBlock_us  = float(parts[6])
        return preTriggerBlock_us, postTriggerBlock_us
    
    def store(self, password: str) -> str:
        """
        Store the current silent stat settings in the controller's non-volatile memory. \n 
        This ensures that the settings are retained even after a power cycle.

        :param password: ethernet controller password for storing settings
        :type password: str

        :returns: controller response
        :rtype: str
        """
        return self._writeReadAndVerifyFeatureSupport(f"SILENCESTAT STORE \"{password}\"", "executed")
    
    def _writeReadAndVerifyFeatureSupport(self, command:str, expectedResponseStart:str) -> str:
        """
        Write a command to the controller, read the response, and verify if the 
        response indicates support for the feature.
        If the feature is not supported, an exception is raised. 

        :param command: The command to send to the controller.
        :type command: str
        :param expectedResponseStart: The expected start of the response indicating support for the feature.
        :type expectedResponseStart: str

        :returns: controller response
        :rtype: str
        """
        try:
            response =self._writeReadAndVerify(command, expectedResponseStart)
            return response  
        except RuntimeError as e:
            response = self._writeReadAndVerify("SILENCESTAT?", " ")
            if response.find("unknown command") != -1:
                errlog = ('Ethernet controller does not support the SilentMode feature')
                raise RuntimeError(errlog) from e
            return response 