
from Licel import  licel_tcpip, licel_TimingConfig, licel_timing
import time

ip = "192.168.178.100"
port = 2055 
def main():
    

    ethernetController = licel_tcpip.EthernetController (ip, port)
    ethernetController.openConnection()
    TimingConfig = licel_TimingConfig.TimingConfig("timing.ini")
    TimingConfig.readConfig()
    TimingControl = licel_timing.TimingController(ethernetController,
                                                      TimingConfig.ChannelsParam)
    
    print(ethernetController.getCapabilities())
    print(TimingControl.getActivetimingBoard())

    for channel in TimingConfig.ChannelsParam:
        if channel.boardID != 0: 
            CAP = 'TIMER' + str(channel.boardID) 
        else:
            CAP = "TIMER"
        
        # Check whether this CAP exists and is marked active before accessing
        if TimingControl.activeBoard.get(CAP) == 'active':
            print(channel)
            print("trigger required:",TimingControl.isExternalTrigrequired(channel))
            if(not TimingControl.isExternalTrigrequired(channel)):
              if (channel.SlaveMode == False):
                channel.LampDelay = (int)(1e9 / channel.repRate)
            channel = TimingControl.CheckTimingGranularity(channel)
            print(TimingControl.setTriggerTiming(channel))
            print(TimingControl.setTriggerMode(channel))
    ethernetController.shutdownConnection()

    

    



if __name__ == "__main__":
    main()
