from Licel import TCP_util, licel_TimingConfig, licel_tcpip
import math
#from dataclasses import dataclass, field




class TimingController(TCP_util.util):

    channelsParam = []
    activeBoard : dict [str, str]= {}
    def __init__(self, ethernetController: licel_tcpip.EthernetController,
                 channelsParam: list[licel_TimingConfig.TimingParameter]) -> None:
        
        self.commandSocket  = ethernetController.commandSocket
        self.PushSocket     = ethernetController.PushSocket
        self.sockFile       = ethernetController.sockFile
        self.pushSockFile   = ethernetController.pushSockFile
        self.channelsParam  = channelsParam 

    def __getTriggerSlaveMode(self, TimingParam: licel_TimingConfig.TimingParameter) -> str: 
        '''
        write True in ``TimingParam.SlaveMode`` 
        if Timerboard has a hardwired external trigger
        '''
        if TimingParam.boardID == 0 :
            resp = self._writeReadAndVerify("TRIGSLAVE?", "TRIGSLAVE")
            if resp.find("1") == -1:
                TimingParam.SlaveMode = False
            else :
                TimingParam.SlaveMode = True
        else :  
            cmd = ("TRIGSLAVE" +  str (TimingParam.boardID)+ "?")
            resp = self._writeReadAndVerify(cmd, "TRIGSLAVE")
            if resp.find("1") == -1:
                TimingParam.SlaveMode = False
            else :
                TimingParam.SlaveMode = True
        return resp

    def isExternalTrigrequired(self, TimingParam: licel_TimingConfig.TimingParameter) -> bool: 
        '''
        raises error if timing board board has a hardwired external trigger , 
        and timing parameter for ``ExternalTrigger`` are set to False
        '''
        self.__getTriggerSlaveMode(TimingParam)

        if (TimingParam.SlaveMode):
            if (not TimingParam.ExternalTrigger):
                raise RuntimeError("the board",TimingParam.boardID,
                                   "has an hardwired external trigger and should"
                                    "be configured with External Trigger true \n")
            return True
        return False
     
    def __getTriggerCycle(self, TimingParam: licel_TimingConfig.TimingParameter) -> str:
        '''
        writes internal internal clock of timing board in 
        ``TimingParam.triggerCycle_ns``, in nano seconds

        :returns: ethernet controller response
        '''
        
        if TimingParam.boardID == 0 :
            cmd = "TRIGCYCLE?"
        else :
            cmd = "TRIGCYCLE" +  str(TimingParam.boardID) + "?"
        resp = self._writeReadAndVerify(cmd, "TRIGCYCLE")
        print(resp)
        TimingParam.triggerCycle_ns = float (resp.split(" ")[1])
        return resp
    
    def __getTriggerScale(self, TimingParam: licel_TimingConfig.TimingParameter) -> str:
        '''
        Query the scaling factors for the counters. 
        writes the scaling in ``TimingParam.scaling``

        :returns: ethernet controller resp
        '''
        if TimingParam.boardID == 0 :
            cmd = "TRIGSCALE?"
        else :
            cmd = "TRIGSCALE" +  str(TimingParam.boardID) + "?"

        resp = self._writeReadAndVerify(cmd, "TRIGSCALE")
        TimingParam.scaling["startDelay"] = int (resp.split(" ")[1])
        TimingParam.scaling["pretrigger"] = int (resp.split(" ")[2])
        TimingParam.scaling["pretriggerLength"] = int (resp.split(" ")[3])
        TimingParam.scaling["qSwitch"]       = int (resp.split(" ")[4])
        TimingParam.scaling["qSwitchLength"] = int (resp.split(" ")[5])
        return resp
    
    def __getTriggerOffset(self, TimingParam: licel_TimingConfig.TimingParameter) -> str: 
        '''
        Query the offsets for the counters
        writes the scaling in ``TimingParam.offset``

        :returns: ethernet controller resp
        '''
        if TimingParam.boardID == 0 :
            cmd = "TRIGOFFSET?"
        else :
            cmd = "TRIGOFFSET" +  str(TimingParam.boardID) + "?"
        resp = self._writeReadAndVerify(cmd, "TRIGOFFSET")
        TimingParam.offset["startDelay"] = int (resp.split(" ")[1])
        TimingParam.offset["pretrigger"] = int (resp.split(" ")[2])
        TimingParam.offset["pretriggerLength"] = int (resp.split(" ")[3])
        TimingParam.offset["qSwitch"]       = int (resp.split(" ")[4])
        TimingParam.offset["qSwitchLength"] = int (resp.split(" ")[5])
        return resp

    def __getDiscreteTime(self, desiredTime: float, paramName: str,
                          TrigParam: licel_TimingConfig.TimingParameter) -> int:
        """Compute the nearest achievable time given timing granularity.

        Implements algorithm from GatingTrigger.pdf subsection 7.1:

        offsetTime = desiredTime - offset * clockPeriod
        cycles = round(offsetTime / (clockPeriod * scale))
        possibleTime = cycles * clockPeriod * scale + offset * clockPeriod + 1ns

        Returns the computed time in nanoseconds as an integer.
        """
        Clock = TrigParam.triggerCycle_ns
        scale = TrigParam.scaling[paramName]
        offset = TrigParam.offset[paramName]
        # time after removing the offset contribution
        offsetTime = float(desiredTime) - float(offset) * float(Clock)
        if offsetTime <= 0:
            offsetTime = 0.0

        # compute number of cycles (round to nearest integer)
        cycles_float = offsetTime / (float(Clock) * float(scale))
        # use round-half-up behaviour: floor(x + 0.5)
        cycles = int(math.floor(cycles_float + 0.5))

        possibleTime = cycles * float(Clock) * float(scale) + float(offset) * float(Clock) + 1.0
        return int(possibleTime)
    
    def CheckTimingGranularity(self, TimingParam:licel_TimingConfig.TimingParameter) -> licel_TimingConfig.TimingParameter:
        param : int = 0
        self.__getTriggerCycle(TimingParam)
        self.__getTriggerScale(TimingParam)
        self.__getTriggerOffset(TimingParam)
        for key in TimingParam.offset : 
            match key :
                case "startDelay":
                    param = TimingParam.LampDelay
                case "pretrigger":
                    param = TimingParam.Pretrigger
                case "pretriggerLength":
                    param = TimingParam.PretriggerLength
                case "qSwitch":      
                    param = TimingParam.QSwitch
                case "qSwitchLength":
                    param = TimingParam.QSwitchLength
                case _:
                    raise RuntimeError("unknown timing parameter", key)
            
            realVal = self.__getDiscreteTime(param, key, TimingParam)
            if (realVal != param):
                print("time adjustment for Board", TimingParam.boardID, key)
                print("desired:" ,param,"ns , real:", realVal, "ns\r\n")
                match key :
                    case "startDelay":
                        TimingParam.LampDelay = realVal
                    case "pretrigger":
                        TimingParam.Pretrigger = realVal
                    case "pretriggerLength":
                        TimingParam.PretriggerLength = realVal
                    case "qSwitch":      
                        TimingParam.QSwitch = realVal
                    case "qSwitchLength":
                        TimingParam.QSwitchLength = realVal

        return TimingParam
    
    def setTriggerTiming(self, TimingParam: licel_TimingConfig.TimingParameter) -> str:
        period_in_ms = int ((1/TimingParam.ExtFreq) * 1000)
        print(period_in_ms)
        if TimingParam.boardID != 0 :
            command = ("TRIGGERTIME"+ str(TimingParam.boardID) + " "+
                       str(TimingParam.LampDelay) + " "+
                       str(TimingParam.Pretrigger) + " "+ 
                       str(TimingParam.PretriggerLength) + " "+
                       str(TimingParam.QSwitch) + " "+
                       str(TimingParam.QSwitchLength) + " " +
                       str(TimingParam.ExtFreq) + " ")
        else : 
            command = ("TRIGGERTIME "+ str(TimingParam.LampDelay) + " " +
                        str(TimingParam.Pretrigger) + " " + 
                        str(TimingParam.PretriggerLength) + " " +
                        str(TimingParam.QSwitch) + " " +
                        str(TimingParam.QSwitchLength) + " " + 
                        str(TimingParam.ExtFreq) + " ")
        print(command)
        resp = self._writeReadAndVerify(command, "executed") 
        return resp
        
    def setTriggerMode(self, TimingParam: licel_TimingConfig.TimingParameter) -> str:
        mode = 0 
        if TimingParam.LampEn : 
            mode = mode +1 
        if TimingParam.ACQ_En:
            mode = mode +2
        if TimingParam.QSwitchEn:
            mode = mode + 4 
        if TimingParam.GatingEn:
            mode = mode + 8
        if TimingParam.ExternalTrigger:
            mode = mode + 16
        
        if TimingParam.boardID != 0: 
            command = ("TRIGGERMODE" + str(TimingParam.boardID) + " "+ str(mode))
        else:
            command = ("TRIGGERMODE " + str(mode))
        print(command)
        resp = self._writeReadAndVerify(command, "executed")
        return resp

    def getActivetimingBoard(self) -> dict[str, str]:
        resp = self._writeReadAndVerify("CAP?","CAP")
        splitted_resp = resp.split(" ")
        for item in splitted_resp: 
            if item.find("TIMER") != -1:
                self.activeBoard[item.strip("\n")] = "active"
            if item.find("MULTIMASTER") != -1:
                self.activeBoard[item.strip("\n")] = "active"
        return self.activeBoard
        
                                     

