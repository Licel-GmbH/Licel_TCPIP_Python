from dataclasses import dataclass, field 
import configparser
from Licel import licel_Config
@dataclass 
class SP32param:

        discriminator     :   int  = field(default =0) 
        noBins            :   int  = field(default =0) 
        binwidth_ns       :   float  = field(default =0)
        HV                :   int  = field(default =0)
        centralWavelength :   float  = field(default =0.0)
        nm_PerChannel     :   float  = field(default =0.0)

class SP32_Config():
    def __init__(self, configFilePath: str):
        self.configFilePath = configFilePath
        self.numDataSets  = 32
        self.SP32param = SP32param()
        self.measurmentInfo = licel_Config.MeasureInfo()
        self.parser = configparser.ConfigParser()

    def readConfig(self):

        self.__getGlobalInfoConfig__()
        self.__getSP32Config__()


    def __getGlobalInfoConfig__(self):  
        """
        get global information from .ini file
        """
        IniFile_read = self.parser.read(self.configFilePath)
        if not IniFile_read:
            raise FileNotFoundError ("Can not open Config file: {}"
                                     .format(self.configFilePath))
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


    def __getSP32Config__(self):
        IniFile_read = self.parser.read(self.configFilePath)
        if not IniFile_read:
            raise FileNotFoundError ("Can not open Config file: {}"
                                    .format(self.configFilePath))
        sections = self.parser.sections()

        for section in sections:
            if (section.find("SP32") >= 0):
                for key in self.parser[section]:
                    if key == 'discriminator' :
                        self.SP32param.discriminator = self.parser.getint(section,key)
                    if key == 'nobins' :
                        self.SP32param.noBins = self.parser.getint(section,key)
                    if key == 'binwidth_ns':
                        self.SP32param.binwidth_ns = float(self.parser[section][key].replace(",","."))
                    if key == 'hv':
                        self.SP32param.HV = self.parser.getint(section,key)
                    if key == 'centralwavelength':  
                        self.SP32param.centralWavelength = float(self.parser[section][key].replace(",","."))
                    if key == 'nm_perchannel':
                        self.SP32param.nm_PerChannel = float(self.parser[section][key].replace(",","."))
        self.parser.clear()