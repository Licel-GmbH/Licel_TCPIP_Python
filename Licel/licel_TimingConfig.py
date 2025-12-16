from dataclasses import dataclass, field
import configparser
    

@dataclass()
class TimingParameter:

    boardID          :   int | None   = field(default =None) #: timing board valid values are 0, 1, 2, 3  
    LampDelay        :   int | None   = field(default =None) #: in internal mode delay between two pulses in ns. 
    Pretrigger       :   int | None   = field(default =None) #: delay between internal or external trigger and pretrigger in ns */
    PretriggerLength :   int | None   = field(default =None) #:  length in  ns of the pretrigger pulse */
    QSwitch          :   int | None   = field(default =None) #: delay between pretrigger start and Q-Switch start in ns*/
    QSwitchLength    :   int | None   = field(default =None) #: length in  ns of the Q-Switch pulse */
    LampEn           :   bool| None   = field(default =None) #: if true a trigger for the laser lamp will be  generated */
    ACQ_En           :   bool| None   = field(default =None) #: if true a trigger for the transient recorder will be generated */
    QSwitchEn        :   bool| None   = field(default =None) #: if true a trigger for the laser Q-Switch will be generated */
    GatingEn         :   bool| None   = field(default =None) #: if true a gating pulse will be generated. The gating pulse starts with the raising edge of
                                                       #: the pretrigger and ends with the falling edge of the Q-Switch Pulse */
    ExternalTrigger  :   bool | None   = field(default =None) #: if true an external trigger will be accepted, if false the internal trigger will be used.
                                                       #: The internal trigger will be controlled via the lampDelay */
    repRate          :   int | None   = field(default =None) #: trigger repetition rate in hz  
    ExtFreq          :   int | None   = field(default =None) #: esimated frequence of the external trigger

    #: //read back parameters from the controller
    SlaveMode        :   bool | None  = field(default =None) #: This board has an hardwired external trigger         
    triggerCycle_ns  :   float | None   = field(default =None) #: length of the master clock in ns */
    #: scaling factors they show how many master clock cycles are used before the counter internally increments*/
    scaling       : dict [str,int] = field(default_factory =
                                           lambda: ({"startDelay": 512,
                                                     "pretrigger": 1,
                                                     "pretriggerLength": 1,
                                                     "qSwitch": 1,
                                                     "qSwitchLength": 1}))
    
    #: offset they show how many master clock cycles are used before the counter first time increments */
    offset       : dict [str,int] = field(default_factory =
                                           lambda: ({"startDelay": 267,
                                                     "pretrigger": 1,
                                                     "pretriggerLength": 1,
                                                     "qSwitch": 1,
                                                     "qSwitchLength": 1})) 

class TimingConfig():

    #: .ini File path. 
    TimingIniConfigPath :str   = " "

    #: List holding the configuration for each Timing board
    ChannelsParam : list[TimingParameter] = [ ]

    #: parser object to parse the .ini configuration file 
    parser = configparser.ConfigParser()

    def __init__(self, TimingIniConfigPath: str):
        self.TimingIniConfigPath = TimingIniConfigPath 

    def readConfig(self):
        '''
        Read the Configuration file and store configuration parameter for each 
        Timming Board in ``ChannelsParam``. \r\n 
        supported config File is ".ini"
        '''
        self.__getTimingConfig__()
    
    def __getTimingConfig__(self):
        """
        get Timming paramters from .ini file
        """

        IniFile_read = self.parser.read(self.TimingIniConfigPath)
        if not IniFile_read:
            raise FileNotFoundError ("Can not open Config file: {}"
                                     .format(self.TimingIniConfigPath))
        sections = self.parser.sections()
        for section in sections:
            tmpParam = TimingParameter()
            if (section.find("TIMER") >= 0 and len(section) >= 5 ):
                if len(section) == 5:
                    tmpParam.boardID = 0
                else:
                    tmpParam.boardID = int(section.removeprefix("TIMER"))
                for key in self.parser[section]:
                    self.__getTimmingParam__(tmpParam, section, key)
                self.ChannelsParam.append(tmpParam)
            del tmpParam

    def __getTimmingParam__(self, tmpParam:TimingParameter, section: str, key: str):
        self.__getMasterTrigger__( tmpParam, section, key)
        self.__getStartDelay__( tmpParam, section, key)
        self.__getQSwitchLength__( tmpParam, section, key)
        self.__getQSwitchDelay__( tmpParam, section, key)
        self.__getPretriggerLength__( tmpParam, section, key)
        self.__getPretriggerDelay__( tmpParam, section, key)
        self.__getRepRate__(tmpParam, section, key)
        self.__getExtFrequency__( tmpParam, section, key)
        self.__getLampEnable__(tmpParam, section, key)
        self.__getQswitchEnable__(tmpParam, section, key)
        self.__getAcqEnable__(tmpParam, section, key)
        self.__getGatingEnable__(tmpParam, section, key)

    def __getMasterTrigger__(self, tmpParam: TimingParameter, section: str, key: str):
        '''
        get Master trigger Enabled/Disabled  
        '''
        if (key == "external_trigger"):
            tmpParam.ExternalTrigger = self.parser.getboolean(section, key)

    def __getStartDelay__(self, tmpParam: TimingParameter, section: str, key: str):
        '''
        get Lamp delay in ns  
        '''
        if (key == "startdelay"):
            val = float(self.parser[section][key].replace(",","."))
            tmpParam.LampDelay = int (val * 1000)
    
    def __getQSwitchLength__(self, tmpParam: TimingParameter, section: str, key: str):
        '''
        get Qswitch pulse length in and convert it to ns   
        '''
        if (key == "q_switch_length_in_microseconds"):
            val = float(self.parser[section][key].replace(",","."))
            tmpParam.QSwitchLength =int (val * 1000) # convert from micro-sec to ns  
    
    def __getQSwitchDelay__(self, tmpParam: TimingParameter, section: str, key: str ):
        '''
        get delay between pretrigger start and Q-Switch start */
        '''
        if (key == "q_switch_delay_minus_pretrig_in_microseconds"):
            val = float(self.parser[section][key].replace(",","."))
            tmpParam.QSwitch =int (val * 1000) # convert from micro-sec to ns
    
    def __getPretriggerLength__(self, tmpParam: TimingParameter, section: str, key: str):
        '''
        get pretrigger length and convert it to ns */
        '''
        if (key == "pretrigger_length_in_microseconds"):
            val = float(self.parser[section][key].replace(",","."))
            tmpParam.PretriggerLength =int (val * 1000) #convert from micro-sec to ns

    def __getPretriggerDelay__(self, tmpParam: TimingParameter, section: str, key: str):
        '''
        get pretrigger delay between internal
        or external trigger and pretrigger in ns *
        '''
        if (key == "pretrigger_delay_in_microseconds"):
            val = float(self.parser[section][key].replace(",","."))
            tmpParam.Pretrigger =int (val * 1000) # convert from micro-sec to ns
    
    def __getRepRate__(self, tmpParam: TimingParameter, section: str, key: str  ):
        '''
        get repetition rate in hertz, parameter will be used only if 
        internal trigger is active otherwise ``estimated frequency`` will be used
        '''
        if (key == "repetition_rate_in_hz"):
            val = float(self.parser[section][key].replace(",","."))
            tmpParam.repRate =int (val ) # convert from micro-sec to ns
    
    def __getExtFrequency__(self, tmpParam: TimingParameter, section: str, key: str):
        '''
        get repetition rate in hertz, parameter will be used only if 
        internal trigger is active otherwise ``estimated frequency`` will be used
        '''
        if (key == "estimatedfrequency_hz"):
            val = float(self.parser[section][key].replace(",","."))
            tmpParam.ExtFreq =int (val) # convert from micro-sec to ns

    def __getLampEnable__(self, tmpParam: TimingParameter, section: str, key: str):
        '''
        get if lamp is enabled in parameter
        '''
        if (key == "enable_lamp"):
            tmpParam.LampEn =self.parser.getboolean(section,key)
    
    def __getQswitchEnable__(self, tmpParam: TimingParameter, section: str, key: str):
        '''
        get if Qswitch is enabled in parameter
        '''
        if (key == "enable_qswitch"):
            tmpParam.QSwitchEn =self.parser.getboolean(section,key)
    
    def __getAcqEnable__(self, tmpParam: TimingParameter, section: str, key: str):
        '''
        get if Acquistion is enabled in parameter
        '''
        if (key == "enable_acquisition"):
            tmpParam.ACQ_En =self.parser.getboolean(section,key)
    
    def __getGatingEnable__(self, tmpParam: TimingParameter, section: str, key: str):
        '''
        get if Acquistion is enabled in parameter
        '''
        if (key == "enable_gating"):
            tmpParam.GatingEn =self.parser.getboolean(section,key)
