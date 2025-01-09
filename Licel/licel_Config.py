from dataclasses import dataclass, field
import configparser
import os
    

@dataclass()
class MeasureInfo:
    ''' 
    this class holds global configuration Info. 
    '''
    szLocation      : str   = field(default =None) #:measurement site 
    nAltitude       : int   = field(default =None) #:altitude above sea level in meters
    dLongitude      : float = field(default =None) #:longitude in degrees
    dLatitude       : float = field(default =None) #:lattitude in degrees
    Zenith          : float = field(default =None) #:Zenith in in degrees 
    Azimuth         : float = field(default =None) #:Azimuth in in degrees 

    cFirstLetter    : str   = field(default =None) #:first letter of the data file
    szOutPath       : str   = field(default =None) #:output directory for data 
    nDataSetNumber  : int   = field(default =None) #:number of datasets into a single file
    
    nMaxShotsL0     : int   = field(default =None)  #:max num of shots for Laser0 
    nMaxShotsL1     : int   = field(default =None)  #:max num of shots for Laser1 
    nMaxShotsL2     : int   = field(default =None)  #:max num of shots for Laser2 
    nMaxShotsL3     : int   = field(default =None)  #:max num of shots for Laser3
    
    repRateL0       : int   = field(default =None) #:repetition rate of Laser0 
    repRateL1       : int   = field(default =None) #:repetition rate of Laser1 
    repRateL2       : int   = field(default =None) #:repetition rate of Laser2 
    repRateL3       : int   = field(default =None) #:repetition rate of Laser3 

    #: dictionary holding global information for laser0. 
    #: dict = {wavelength1 : polarization1, wavelength2: polarizaton2}
    Laser0_globalInfo     :dict[float, int] = field(default_factory = lambda: ({0.0: 0}))
    #: dictionary holding global information for laser1.  
    #: dict = {wavelength1 : polarization1, wavelength2: polarizaton2}
    Laser1_globalInfo     :dict[float, int] = field(default_factory = lambda: ({0.0: 0}))
    #: dictionary holding global information for laser2. 
    #: dict = {wavelength1 : polarization1, wavelength2: polarizaton2}
    Laser2_globalInfo     :dict[float, int] = field(default_factory = lambda: ({0.0: 0}))
    #: dictionary holding global information for laser3.
    #: dict = {wavelength1 : polarization1, wavelength2: polarizaton2}
    Laser3_globalInfo     :dict[float, int] = field(default_factory = lambda: ({0.0: 0}))




@dataclass()
class TrConfig: 
    #: transient recorder address 
    nTransientRecorder:   int = field(default =None) 
    #: analog input range 0 for 500mV, 1 for 100mV, 2 for 20mV                        
    nRange            :   int = field(default =None) 
    #: Discriminator level between 0 and 63              
    discriminator     :   int   = field(default =None) 
    #: shot limit for the Transient recorder, arbitrary number between 2 and 64K. 
    shotLimit         :   int   = field(default =None)
    #: 1 for pretrigger enabled, 0 for pretrigger disabled 
    pretrigger        :   int   = field(default =None) 
    #: Set the frequency divider, it changes the sampling rate before the summation
    #: possible values are 0-7
    freqDivider       :   int   = field(default =None)
    #: Sets the damping state to either on or off. 1 to turn on the Damping mode. 
    #: 0 to turn off the Damping mode.
    threshold         :   int   = field(default =None)

    #: holds the laser polarization for the analogue memory 
    #: none, vertical, horizontal, right circular, left circular 0|1|2|3|4   
    analoguePolarisation : dict[str, int]  = field(default_factory = lambda: ({"A": 0,
                                                                               "B":0,
                                                                               "C":0,
                                                                               "D":0})) 
    #: holds the laser polarization for the photon counting memory 
    #: none, vertical, horizontal, right circular, left circular 0|1|2|3|4  
    pcPolarisation  : dict[str, int]  = field(default_factory = lambda: ({"A": 0,
                                                                          "B":0,
                                                                          "C":0,
                                                                          "D":0}))   
      
    #: holds information if the analogue acquisition for each memory is enabled 
    analogueEnabled : dict[str, bool] = field(default_factory = lambda: ({"A":False,
                                                                          "B":False,
                                                                          "C":False,
                                                                          "D":False})) 
      
    #: holds information if the photon counting acquisition for each memory is enabled 
    pcEnabled       : dict[str, bool] =  field(default_factory = lambda:({"A": False,
                                                                          "B":False, 
                                                                          "C":False,
                                                                          "D":False})) 
    #: holds the number of analogue bins to acquire for each memory 
    analogueBins    : dict[str, int]  =  field(default_factory = lambda: ({"A": 0,
                                                                           "B":0,
                                                                           "C":0,
                                                                           "D":0})) 
    #: holds the number of photon counting bins to acquire for each memory
    pcBins          : dict[str, int]  =  field(default_factory = lambda: ({"A": 0,
                                                                           "B":0,
                                                                           "C":0,
                                                                           "D":0})) 
    #: holds information for the wavelength assigned to each analogue memory
    analogueWavelength : dict[str, float] =  field(default_factory = lambda: ({"A": 0.0,
                                                                               "B":0.0,
                                                                               "C":0.0,
                                                                               "D":0.0}))
    #: holds information for the wavelength assigned to each photon counting memory
    pcWavelength      : dict[str, float] =  field(default_factory = lambda: ({"A": 0.0,
                                                                              "B":0.0,
                                                                              "C":0.0,
                                                                              "D":0.0}))
     
    laserAssignment   : dict[str, int]  =  field(default_factory = lambda: ({"A": 0,
                                                                             "B":0,
                                                                             "C":0,
                                                                             "D":0}))
    #: holds the Voltage (in Volt) for each PMT assigned to analogue memory.
    #: for example PMT assigned to analogue memory A has 850 Volt.         
    #: pmVoltageAnalogue = {"A": 850, "B": 0, "C": 0, "D": 0}     
    pmVoltageAnalogue : dict[str, float] =  field(default_factory = lambda: ({"A": 0.0,
                                                                              "B":0.0,
                                                                              "C":0.0,
                                                                              "D":0.0}))
    #: holds the Voltage (in Volt) for each PMT assigned to pc memory.
    #: for example PMT assigned to pc memory B has 800 Volt. 
    #: pmVoltagePC = {"A": 0, "B": 800, "C": 0, "D": 0}   
    pmVoltagePC : dict[str, float] =  field(default_factory = lambda: ({"A": 0.0,
                                                                        "B":0.0,
                                                                        "C":0.0,
                                                                        "D":0.0}))

    #: holds information if the any global triggers is blocked  
    blockedTrig : dict[str, bool] = field(default_factory = lambda: ({"A":False,
                                                                      "B":False,
                                                                      "C":False,
                                                                      "D":False})) 
     
    def __post_init__(self):
        if self.discriminator is None:
            self.discriminator = 'not defined'
        if self.nRange is None:
            self.nRange = 'not defined'

class Config():
    #: .ini File path. 
    acquisIniConfigPath  = " "
    #: global Measurement info configuration  
    measurmentInfo = MeasureInfo()
    #: List holding the configuration for each transient recorder
    TrConfigs : [TrConfig] = [ ]
    #: holds the total number of datasets to be read, analogue and photon counting 
    numDataSets = 0 
    #: parser object to parse the .ini configuration file 
    parser = configparser.ConfigParser()

    def __init__(self, acquisIniPath = None ):
        self.acquisIniConfigPath = acquisIniPath 

    def readConfig(self):
        '''
        Read the Configuration file and store configuration parameter for each transient
        recorder in ``TrConfigs`` and global measurement information in ``measurementInfo`` . \r\n 
        supported config File is ".ini"
        '''
        self.__getGlobalInfoConfig__()
        self.__getAcquisConfig__() 


        return self.TrConfigs  

    def __getGlobalInfoConfig__(self):  
        """
        get global information from .ini file
        """
        IniFile_read = self.parser.read(self.acquisIniConfigPath)
        if not IniFile_read:
            raise FileNotFoundError ("Can not open Config file: {}"
                                     .format(self.acquisIniConfigPath))
        sections = self.parser.sections()
        tmpWavelength = 0.0
        tmpPolarization = 0
        for section in sections:
            if section.find("Laser1") >= 0:
               self.measurmentInfo.Laser0_globalInfo.pop(0.0)
               for key in self.parser[section]:
                        if key.find("wavelength") > -1: 
                            tmpWavelength = float(self.parser[section][key].replace(",","."))
                        if key.find("polarization") > -1:
                            tmpPolarization = self.parser.getint(section,key)
                        self.measurmentInfo.Laser0_globalInfo.update({tmpWavelength : tmpPolarization})

            if section.find("Laser2") >= 0:
               self.measurmentInfo.Laser1_globalInfo.pop(0.0)
               for key in self.parser[section]:
                        if key.find("wavelength") > -1: 
                            tmpWavelength = float(self.parser[section][key].replace(",","."))
                        if key.find("polarization") > -1:
                            tmpPolarization = self.parser.getint(section,key)
                        self.measurmentInfo.Laser1_globalInfo.update({tmpWavelength : tmpPolarization})

            if section.find("Laser3") >= 0:
               self.measurmentInfo.Laser2_globalInfo.pop(0.0)
               for key in self.parser[section]:
                        if key.find("wavelength") > -1: 
                            tmpWavelength = float(self.parser[section][key].replace(",","."))
                        if key.find("polarization") > -1:
                            tmpPolarization = self.parser.getint(section,key)
                        self.measurmentInfo.Laser2_globalInfo.update({tmpWavelength : tmpPolarization})

            if (section == "global_info" ):
               for key in self.parser[section]:
                    if key.find("location") >= 0: 
                       self.measurmentInfo.szLocation = self.parser[section][key].replace('"', "")
                    if key.find("longitude") >= 0: 
                        self.measurmentInfo.dLongitude = float(self.parser[section][key].replace(",",".")) 
                    if key.find("latitude") >= 0: 
                        self.measurmentInfo.dLatitude = float(self.parser[section][key].replace(",","."))
                    if key.find("azimuth") >= 0: 
                        self.measurmentInfo.Azimuth   = float(self.parser[section][key].replace(",",".")) 
                    if key.find("height_asl") >= 0: 
                        self.measurmentInfo.nAltitude = int(float(self.parser[section][key].replace(",","."))) 
                    if key.find("working_dir") >= 0: 
                        self.measurmentInfo.szOutPath = self.parser[section][key].replace('"', "") 
                    if key.find("first_letter") >= 0: 
                        self.measurmentInfo.cFirstLetter = self.parser[section][key].replace('"', "") 
                    if key.find("frequency1") >= 0: 
                        self.measurmentInfo.repRateL0 = int(float(self.parser[section][key].replace(",","."))) 
                    if key.find("frequency2") >= 0: 
                        self.measurmentInfo.repRateL1 = int(float(self.parser[section][key].replace(",","."))) 
                    if key.find("frequency3") >= 0: 
                        self.measurmentInfo.repRateL2 = int(float(self.parser[section][key].replace(",","."))) 
                    if key.find("zenith") >= 0: 
                        self.measurmentInfo.Zenith = float(self.parser[section][key].replace(",","."))
        self.parser.clear()

    def __getAcquisConfig__(self): 
        '''
        Get acquisition parameter for each transient recorder in .ini file 
        '''
        self.parser.read(self.acquisIniConfigPath)
        sections = self.parser.sections()
        i = 0
        for section in sections:
            if (section.find("TR") >= 0 and len(section) > 2):
                tmpDataset = TrConfig()
                tmpDataset.nTransientRecorder = int(section.removeprefix("TR"))
                for key in self.parser[section]:
                    if (key == "discriminator"): 
                        tmpDataset.discriminator = self.parser.getint(section,key)
                    if (key == "range"): 
                        range = self.parser.getint(section,key)
                        tmpDataset.nRange =  self.__convertRangeToHumanReadable__(range)  
                    if (key == "SquaredData"): 
                        tmpDataset.squaredData = self.parser.getboolean(section,key)
                    if (key == "sqr-bins"): 
                        tmpDataset.squaredBins = self.parser.getint(section,key)

                    self.__getActiveAnalogueMem__(tmpDataset,section,key)
                    self.__getActivePCMem__(tmpDataset,section,key)
                    self.__getAnaloguePolarization__(tmpDataset,section,key)
                    self.__getPcPolarization__(tmpDataset,section,key)
                    self.__getAnalogueBins__(tmpDataset,section,key) 
                    self.__getPcBins__(tmpDataset,section,key)
                    self.__getAnalogueWavelength__(tmpDataset,section,key)
                    self.__getPcWavelength__(tmpDataset,section,key)
                    self.__getLaserAssignment__(tmpDataset, section, key) 
                    self.__getPMVoltageAnalogue__(tmpDataset, section, key)
                    self.__getPMVoltagePC__(tmpDataset, section, key) 
                    self.__getShotLimit__(tmpDataset, section, key) 
                    self.__getPretrigger__(tmpDataset, section, key) 
                    self.__getfreqDiv__(tmpDataset, section, key) 
                    self.__getThreshold__(tmpDataset, section, key) 
                    self.__getBlockedTrigger__(tmpDataset,section,key)

                self.TrConfigs.append(tmpDataset)
                del tmpDataset
        
    def __getActiveAnalogueMem__(self,tmpDataset,section,key):
        ''' 
        get active memory for analogue data. 
        we will acquire analogue  data set for the active memory 
        '''
        if (key == "analoga"): 
            tmpDataset.analogueEnabled["A"] = self.parser.getboolean(section,key)
        if (key == "analog b"): 
            tmpDataset.analogueEnabled["B"] = self.parser.getboolean(section,key)
        if (key == "analog c"): 
            tmpDataset.analogueEnabled["C"] = self.parser.getboolean(section,key)
        if (key == "analogd"): 
            tmpDataset.analogueEnabled["D"] = self.parser.getboolean(section,key)

    def __getBlockedTrigger__(self,tmpDataset,section,key):
        ''' 
        get blocked global trigger for memory each memory.
        '''
        if (key == "blocktriga"): 
            tmpDataset.blockedTrig["A"] = self.parser.getboolean(section,key)
        if (key == "blocktrigb"): 
            tmpDataset.blockedTrig["B"] = self.parser.getboolean(section,key)
        if (key == "blocktrigc"): 
            tmpDataset.blockedTrig["C"] = self.parser.getboolean(section,key)
        if (key == "blocktrigd"): 
            tmpDataset.blockedTrig["D"] = self.parser.getboolean(section,key)

    def __getActivePCMem__(self,tmpDataset,section,key):
        ''' get active memory for photon counting data. 
            we will acquire photon counting data set for the active memory 
        '''
        if (key == "pc a"): 
            tmpDataset.pcEnabled["A"] = self.parser.getboolean(section,key)
        if (key == "pc b"): 
            tmpDataset.pcEnabled["B"] = self.parser.getboolean(section,key)
        if (key == "pc c"): 
            tmpDataset.pcEnabled["C"] = self.parser.getboolean(section,key)
        if (key == "pc d"): 
            tmpDataset.pcEnabled["D"] = self.parser.getboolean(section,key)
    
    def __getAnaloguePolarization__(self,tmpDataset,section,key):
        ''' get the laser polarisation assigned to each analogue memory '''

        if (key == "polarisationa"):
            tmpDataset.analoguePolarisation["A"] = self.parser.getint(section,key)
        if (key == "polarisationb"):
            tmpDataset.analoguePolarisation["B"] = self.parser.getint(section,key)
        if (key == "polarisationc"):
            tmpDataset.analoguePolarisation["C"] = self.parser.getint(section,key)
        if (key == "polarisationd"):
            tmpDataset.analoguePolarisation["D"] = self.parser.getint(section,key)
    
    def __getPcPolarization__(self,tmpDataset,section,key):
        ''' get the laser polarisation assigned to each photoncounting memory '''
        if (key == "polarisationapc"):
            tmpDataset.pcPolarisation["A"] = self.parser.getint(section,key)
        if (key == "polarisationbpc"):
            tmpDataset.pcPolarisation["B"] = self.parser.getint(section,key)
        if (key == "polarisationcpc"):
            tmpDataset.pcPolarisation["C"] = self.parser.getint(section,key)
        if (key == "polarisationdpc"):
            tmpDataset.pcPolarisation["D"] = self.parser.getint(section,key)

    def __getAnalogueBins__(self,tmpDataset,section,key): 
        ''' get the number of bins to acquire for each analogue memory '''
        if (key == "a-binsa"): 
            tmpDataset.analogueBins["A"] = self.parser.getint(section,key)
        if (key == "a-binsb"): 
            tmpDataset.analogueBins["B"] = self.parser.getint(section,key)
        if (key == "a-binsc"): 
            tmpDataset.analogueBins["C"] = self.parser.getint(section,key)
        if (key == "a-binsd"): 
            tmpDataset.analogueBins["D"] = self.parser.getint(section,key)
    
    def __getPcBins__(self,tmpDataset,section,key):
        ''' get the number of bins to acquire for each pc memory '''
        if (key == "p-binsa"): 
            tmpDataset.pcBins["A"] = self.parser.getint(section,key)
        if (key == "p-binsb"): 
            tmpDataset.pcBins["B"] = self.parser.getint(section,key)
        if (key == "p-binsc"): 
            tmpDataset.pcBins["C"] = self.parser.getint(section,key)
        if (key == "p-binsd"): 
            tmpDataset.pcBins["D"] = self.parser.getint(section,key)

    def __getAnalogueWavelength__(self,tmpDataset,section,key):
        ''' get laser wavelength for each analogue memory '''
        if (key == "wavelengtha"): 
            tmpDataset.analogueWavelength["A"] = float(self.parser[section][key].replace(",","."))
        if (key == "wavelengthb"): 
            tmpDataset.analogueWavelength["B"] = float(self.parser[section][key].replace(",","."))
        if (key == "wavelengthc"): 
            tmpDataset.analogueWavelength["C"] = float(self.parser[section][key].replace(",","."))
        if (key == "wavelengthd"): 
            tmpDataset.analogueWavelength["D"] = float(self.parser[section][key].replace(",","."))
    
    def __getPcWavelength__(self,tmpDataset,section,key):
        ''' get laser wavelength for each photoncounting memory '''
        if (key == "wavelengthapc"): 
            tmpDataset.pcWavelength["A"] = float(self.parser[section][key].replace(",","."))
        if (key == "wavelengthbpc"): 
            tmpDataset.pcWavelength["B"] = float(self.parser[section][key].replace(",","."))
        if (key == "wavelengthcpc"): 
            tmpDataset.pcWavelength["C"] = float(self.parser[section][key].replace(",","."))
        if (key == "wavelengthdpc"): 
            tmpDataset.pcWavelength["D"] = float(self.parser[section][key].replace(",","."))

    def __getLaserAssignment__(self, tmpDataset, section, key):  
        ''' get the laser assigned to each memory '''
        if (key == "lasera"): 
            tmpDataset.laserAssignment["A"] = self.parser.getint(section,key)
        if (key == "laserb"): 
            tmpDataset.laserAssignment["B"] = self.parser.getint(section,key)
        if (key == "laserc"): 
            tmpDataset.laserAssignment["C"] = self.parser.getint(section,key)
        if (key == "laserd"): 
            tmpDataset.laserAssignment["D"] = self.parser.getint(section,key)

    def __getPMVoltageAnalogue__(self, tmpDataset, section, key):
        ''' get PMT voltage for analogue memory'''
        if (key == "pm"): 
            tmpDataset.pmVoltageAnalogue["A"] = float(self.parser[section][key].replace(",","."))
        if (key == "pm2"): 
            tmpDataset.pmVoltageAnalogue["B"] = float(self.parser[section][key].replace(",","."))
        if (key == "pm3"): 
            tmpDataset.pmVoltageAnalogue["C"] = float(self.parser[section][key].replace(",","."))
        if (key == "pm4"): 
            tmpDataset.pmVoltageAnalogue["D"] = float(self.parser[section][key].replace(",","."))

    def __getPMVoltagePC__(self, tmpDataset, section, key):
        ''' get PMT voltage for pc memory'''
        if (key == "pm1pc"): 
            tmpDataset.pmVoltagePC["A"] = float(self.parser[section][key].replace(",","."))
        if (key == "pm2pc"): 
            tmpDataset.pmVoltagePC["B"] = float(self.parser[section][key].replace(",","."))
        if (key == "pm3pc"): 
            tmpDataset.pmVoltagePC["C"] = float(self.parser[section][key].replace(",","."))
        if (key == "pm4pc"): 
            tmpDataset.pmVoltagePC["D"] = float(self.parser[section][key].replace(",","."))

    def __convertRangeToHumanReadable__(self,range): 
        ''' convert range to human readable number'''
        if range == 0:
            return 500
        elif range == 1: 
            return 100
        elif range == 2:
            return 20 
        else :
            raise Exception('Range must be : "0"-> 500mV, "1"-> 100mV, "2"-> 20mV \r\n')

    def __getShotLimit__(self, tmpDataset, section, key):
        ''' get shot limit from .ini file '''
        if (key == "shotlimit"): 
            tmpDataset.shotLimit = self.parser.getint(section,key)
    
    def __getPretrigger__(self, tmpDataset, section, key):
        ''' get if pretrigger enabled from .ini file '''
        if (key == "pretrigger"): 
            tmpDataset.pretrigger = self.parser.getint(section,key)
    
    def __getfreqDiv__(self, tmpDataset, section, key):
        ''' get frequency divider from .ini file '''
        if (key == "freqdivider"): 
            tmpDataset.freqDivider = self.parser.getint(section,key)
    
    def __getThreshold__(self, tmpDataset, section, key):
        ''' get threshold from .ini file'''
        if (key == "threshold"): 
            tmpDataset.threshold = self.parser.getint(section,key)