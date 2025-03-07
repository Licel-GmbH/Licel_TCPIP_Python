from Licel import TCP_util

class  photomultiplier(TCP_util.util):

    run_PushThreads = False
    
    def __init__(self, ethernetController) -> None:
        
        self.commandSocket = ethernetController.commandSocket 
        self.sockFile      = ethernetController.sockFile

    def setHV(self, device : int, voltage : int) -> str:
        """
        set voltage for the pmt 

        :param device:  pmt device number
        :type device: int 

        :param voltage: desired pmt voltage 
        :type voltage: int

        :returns: controller response 
        :rtype: str
        """
        command = ("PMTG {device:2d} {voltage:4d}"
                   .format(device = device,
                           voltage = voltage))
        self.writeCommand(command)
        resp= self.readResponse()
        return resp

    def getHV(self, device : int) -> str:
        """
        get Voltage of the pmt 

        :param device:  pmt device number
        :type device: int 


        :returns: controller response containing the pmt high voltage 
        :rtype: str
        """
        command = ("PMT? {device:4d}"
                   .format(device = device))
        self.writeCommand(command)
        resp= self.readResponse()
        return resp

    def isPMTinstalled(self, device):
        """
        verifies if the pmt is correctly installed. \n
        1. Set the high voltages PMTs ``device`` to 0 \n
        2. Request high voltage. When a PMT reply contains around 356 V
        the corresponding cassette/PMT is not installed.

        :param device:  pmt device number
        :type device: int 

        :returns: True when pmt corresponding to ``device`` is installed.   
        :rtype: bool
        """
        resp = self.setHV(device,0)
        voltage = self.getHV(device).split(" ")[1]
        try:
            if ((float (voltage) <360) and (float(voltage) >350)): 
                return False
            else : 
                return True
        except: 
            #returned response from getHV() PMT not available
            return False
        
    def listInstalledPMT(self):
        """
        verifies if all PMT's are correctly installed.

        :returns: dict holding information of which pmt is installed. 
        :rtype: dict{pmt number : Installed/Not installed}
        """
        pmtDict = {}
        for i in range(0,16):
            if self.isPMTinstalled(i):
                pmtDict[i] = "Installed"
            else : 
                pmtDict[i] = "Not installed"

        return pmtDict