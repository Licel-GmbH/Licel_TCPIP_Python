from Licel import TCP_util
from dataclasses import dataclass, field
import configparser
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from Licel import licel_tcpip

@dataclass
class LaserSyncParameter:

    #: The internal trigger frequency is controlled via the number
    #:  of cycles of the master oscillator, each cycle is 200ns long 
    MasterCycles     : int | None = field(default = None)
    #:Then for each laser one can give the number of omitted master cycle triggers.
    #:Giving there 0 will output a trigger on each master trigger,
    #:giving 1 will produce a trigger only on every second trigge
    Laser1Omit       : int | None = field(default = None)
    #:counting of the omitted pulses begins with the offset instead of 0.
    #:This ensures that for higher numbers of omitted pulses,
    #:different lasers can be assigned to use different master triggers.
    Laser1Offset     : int | None = field(default = None)
    Laser2Omit       : int | None = field(default = None)
    Laser2Offset     : int | None = field(default = None)
    Laser3Omit       : int | None = field(default = None)
    Laser3Offset     : int | None = field(default = None)
    #: if true an external trigger will be accepted, if false the internal trigger will be used.
    #: The internal trigger will be controlled via the ``MasterCycles`` 
    ExternalTrigger  : bool | None = field(default = None)
    ActiveLasers     : dict [str,bool | None] = field(default_factory =
                                            lambda: ({"Laser1": None,
                                                      "Laser2": None,
                                                      "Laser3": None}))

class LaserSyncConfig():
    #: .ini File path. 
    LaserSyncIniConfigPath  = " "

    Config :LaserSyncParameter 
    #: parser object to parse the .ini configuration file 
    parser = configparser.ConfigParser()

    def __init__(self, LaserSyncIniConfigPath : str) -> None:
        self.LaserSyncIniConfigPath = LaserSyncIniConfigPath 

    def readConfig(self):
        '''
        Read the Configuration file and store configuration parameter for 
        LaserSync in ``Config``. \r\n 
        supported config File is ".ini"
        '''
        self.__LaserSyncConfig__()
    
    def __LaserSyncConfig__(self):
        " get LaserSync paramter from .ini file"
        IniFile_read = self.parser.read(self.LaserSyncIniConfigPath)
        tmpParam:LaserSyncParameter = LaserSyncParameter()
        if not IniFile_read:
            raise FileNotFoundError ("Can not open Config file: {}"
                                     .format(self.LaserSyncIniConfigPath))
        sections = self.parser.sections()
        for section in sections:
            if (section.find("MULTIMASTER") >= 0 ):
                #tmpParam: LaserSyncParameter = LaserSyncParameter()
                for key in self.parser[section]:
                    self.__getLaserSyncParam__(tmpParam, section, key)
        self.Config = tmpParam

    def __getLaserSyncParam__(self, tmpParam:LaserSyncParameter,
                              section: str, key: str):
        if (key == "mastercycles"):
            tmpParam.MasterCycles = self.parser.getint(section, key)  
        if (key == "laser1omit"):
            tmpParam.Laser1Omit = self.parser.getint(section, key)
        if (key == "laser1offset"):
            tmpParam.Laser1Offset = self.parser.getint(section, key)
        if (key == "laser2omit"):
            tmpParam.Laser2Omit = self.parser.getint(section, key)
        if (key == "laser2offset"):
            tmpParam.Laser2Offset = self.parser.getint(section, key)
        if (key == "laser3omit"):
            tmpParam.Laser3Omit = self.parser.getint(section, key)
        if (key == "laser3offset"):
            tmpParam.Laser3Offset = self.parser.getint(section, key)
        if (key == "laser3offset"):
            tmpParam.Laser3Offset = self.parser.getint(section, key)
        if (key == "laser1"):
            tmpParam.ActiveLasers["Laser1"] = self.parser.getboolean(section, key)
        if (key == "laser2"):
            tmpParam.ActiveLasers["Laser2"] = self.parser.getboolean(section, key)
        if (key == "laser3"):
            tmpParam.ActiveLasers["Laser3"] = self.parser.getboolean(section, key)
        if (key == "external_trigger"):
            tmpParam.ExternalTrigger = self.parser.getboolean(section, key)

class LaserSync(TCP_util.util): 
    
    def __init__(self, ethernetController: 'licel_tcpip.EthernetController') -> None:
        
        self.commandSocket  = ethernetController.commandSocket
        self.PushSocket     = ethernetController.PushSocket
        self.sockFile       = ethernetController.sockFile
        self.pushSockFile   = ethernetController.pushSockFile


    def setparam(self, param: LaserSyncParameter) -> str:
        mode = self.__calcTriggerMode__(param)
        cmd = (f"MULTIMASTER {param.MasterCycles} {param.Laser1Omit} "
            f"{param.Laser1Offset} {param.Laser2Omit} {param.Laser2Offset} "
            f"{param.Laser3Omit} {param.Laser3Offset} {mode} ")
        resp = self._writeReadAndVerify(cmd, "executed")
        print(cmd)
        return resp
    
    def getStoredConfig(self):
        resp = self._writeReadAndVerify("MULTIMASTERSTORE?", "MULTIMASTERSTORE")
        return resp

    def storeConfig(self,param: LaserSyncParameter, password: str) -> str:
        mode = self.__calcTriggerMode__(param)
        cmd = (f"MULTIMASTERSTORE {param.MasterCycles} {param.Laser1Omit} "
              f"{param.Laser1Offset} {param.Laser2Omit} {param.Laser2Offset} "
              f"{param.Laser3Omit} {param.Laser3Offset} {mode} \"{password}\" ")
        print(cmd)
        resp = self._writeReadAndVerify(cmd, "executed")
        return resp

    def __calcTriggerMode__(self, param: 'LaserSyncParameter') -> int:
        mode = 8
        if param.ActiveLasers["Laser1"]:
            mode = mode + 1       
        if param.ActiveLasers["Laser2"]:
            mode = mode + 2
        if param.ActiveLasers["Laser3"]:
            mode = mode + 4
        if not param.ExternalTrigger: 
            mode = mode + 16
        return mode
            
