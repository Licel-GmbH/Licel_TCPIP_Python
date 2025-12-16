from Licel import licel_tcpip, licel_SP32, licel_SP32_Config
import time
from datetime import datetime
import argparse


CURRENTLIMIT = 0.400 #in mA 

def commandLineInterface():
    argparser = argparse.ArgumentParser(description='SP32 example ')
    argparser.add_argument('--ip', type=str, default = "10.49.234.234",
                            help='ethernet controller ip address')
    argparser.add_argument('--port', type=int, default=2055,
                            help='ethernet controller command port')
    argparser.add_argument('--shots', type=int, default=100,
                            help='number of shots to acquire per run')
    argparser.add_argument('--acq', type=int, default=10,
                            help='number of acquisition to perform')
    args = argparser.parse_args()
    return args

def AcquireAndSave(sp32: licel_SP32.SP32, Config: licel_SP32_Config.SP32_Config,
                   Shots_To_Acquire: int):
    
    starttime = datetime.now()
    sp32.startAcquisition(Shots_To_Acquire)


    state,  shots, targetshots, current, timestamp = sp32.getStatus()
    while state != 'Idle':
        state,  shots, targetshots, current, timestamp = sp32.getStatus()
        time.sleep(0.1)
        if current > CURRENTLIMIT:
            print(f"Current limit exceeded: {current} mA. Setting HV to 0")
            sp32.setHV(0)
            sp32.stopAcquisition()
            raise Exception(f"Current limit exceeded: {current} mA. Setting HV to 0") 

    shots,data = sp32.getData()
    stoptime = datetime.now()
    sp32.saveSP32Data(Config, starttime, stoptime,"EH",shots, data)
    return shots,data

def main():
    myArguments = commandLineInterface()    
    ip = myArguments.ip
    port = myArguments.port
    Shots_To_Acquire = myArguments.shots
    RUNS = myArguments.acq

    ethernetController = licel_tcpip.EthernetController (ip, port)
    sp32 = licel_SP32.SP32(ethernetController)
    Config = licel_SP32_Config.SP32_Config("SP32.ini")
    Config.readConfig()
    ethernetController.openConnection()

    print("*** GET SP32 hardware informations ****")
    print(ethernetController.getID())
    print(sp32.getHardwareID())
    print(sp32.getCapabilites())
    print(sp32.getCurrent())
    print(sp32.getDieTemperature())
    print(sp32.getPCBTemperature())
    print(ethernetController.getMilliSecs())
    print("*** CONFIGURE SP32 PARAMETERS ****")
    print(sp32.setDiscriminator(Config.SP32param.discriminator))
    print(sp32.setHV(Config.SP32param.HV))
    time.sleep(0.1)
    print(sp32.getHV())
    print(sp32.setTimeResoultion(Config.SP32param.binwidth_ns))
    print(sp32.setRange(Config.SP32param.noBins))
    print(sp32.closeShutter())
    print(sp32.getShutterPosition())
    print(sp32.openShutter())
    print(sp32.getShutterPosition())
    

    print("****************** Starting Acquisition ***********************")
    print(sp32.stopAcquisition())
    cycle = 0
    while cycle < RUNS: 
        AcquireAndSave(sp32, Config, Shots_To_Acquire)
        cycle += 1  
    print("******************Acquisition Finished, Shutting down...*************")
    print(sp32.setHV(0))
    ethernetController.shutdownConnection() 
if __name__ == "__main__":
    main()