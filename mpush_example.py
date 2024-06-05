#! python3.10
'''
Copyright ©: Licel GmbH 

Usage:
python3 mpush_example.py --ip <ip> --port <port>  --acq <num acquis> --shots <num shots>
                 --acquis_per_file <acquis per file> --log
'''
from Licel import licel_tcpip, licel_data, licel_Config
from datetime import datetime
import argparse

logFilePath = 'mpush_log.txt' # log file

def commandLineInterface():
    argparser = argparse.ArgumentParser(description='Mpush example ')
    argparser.add_argument('--ip', type=str, default = "10.49.234.234",
                    help='ethernet controller ip address')
    argparser.add_argument('--port', type=int, default=2055,
                    help='ethernet controller command port')
    argparser.add_argument('--acq', type=int, default=10,
                    help='number of acquisitions')
    argparser.add_argument('--shots', type=int,  default=15,
                    help='number of shots per acquisition')
    argparser.add_argument('--log', type=bool, default=False,
                           action=argparse.BooleanOptionalAction,
                    help='log the push data when error occurs in push buffer raw data ')
    argparser.add_argument('--acquis_per_file', type=int, nargs='?', default=10,
                    help='maximal number of acquisitions to write in a single file')
    
    args = argparser.parse_args()
    return args 

def main():
    
    #initialize acquisition parameters using parameters passed from command line interface
    myArguments = commandLineInterface()
    ip = myArguments.ip
    port = myArguments.port
    desiredShots = myArguments.shots
    ACQUISTION_CYCLES = myArguments.acq
    ACQUISPERFILE = myArguments.acquis_per_file 
    LOGPUSHDATA = myArguments.log 

    ethernetController = licel_tcpip.licelTCP (ip, port)
    dataParser = licel_data.DataParser()
    ConfigInfo = licel_Config.Config("Acquis.ini")
    pushBuffer = bytearray()
    
    ConfigInfo.readConfig()
    ethernetController.openConnection()
    ethernetController.openPushConnection()

    bigEndianTimeStamp = False
    Idn = ethernetController.getID()
    if (Idn.find("ColdFireEthernet") != -1) : 
        bigEndianTimeStamp = True 

    Tr = ethernetController.listInstalledTr()   
    TRHardwareInfos = ethernetController.getTrHardwareInfo(Tr, ConfigInfo)
    Tr.configureHardware(ConfigInfo)
    
    print(ethernetController.MPushStartFromConfig(desiredShots, ConfigInfo, TRHardwareInfos))

    startTime =  datetime.now()
    print("*** Started mpush acqusition at:",startTime, " *** \r\n")
    cycle_count = 0
    while (cycle_count < ACQUISTION_CYCLES):
        
        startTime =  datetime.now()
        ethernetController.recvPushData(pushBuffer, ConfigInfo.BufferSize) 
        stopTime =  datetime.now()

        (dataValid,
         dataSets,
         time_stamp,
         analogue_shots,
         pc_shots) = dataParser.parseDataFromBuffer(pushBuffer,
                                                    ConfigInfo,
                                                    bigEndianTimeStamp,
                                                    desiredShots, 
                                                    TRHardwareInfos)
        if (dataValid): 
            cycle_count += 1
            dataParser.saveFile(dataSets,
                                ConfigInfo,
                                startTime,stopTime,
                                TRHardwareInfos,
                                time_stamp,
                                analogue_shots, 
                                pc_shots,
                                desiredShots,
                                ACQUISPERFILE ) 
        else :
            if (LOGPUSHDATA): 
                controllerTimeMs = ethernetController.getMilliSecs()
                print("Invalid data received with timestamp:",controllerTimeMs)
                dataParser.pushDataLog(logFilePath,
                                       pushBuffer,
                                       Idn,
                                       controllerTimeMs,
                                       ConfigInfo)
            # if data is not valid clear buffer until next occurrence of xff xff 
            dataParser.removeInvalidDataFromBuffer(pushBuffer)

    ethernetController.MPushStop(Tr, ConfigInfo)
    ethernetController.shutdownConnection()
    ethernetController.shutdownPushConnection()

    stopTime =  datetime.now()
    print("{} acquisition written to {} \r\n"
          .format(ACQUISTION_CYCLES, ConfigInfo.measurmentInfo.szOutPath))
    print("*** Stopped mpush acquisition at:",stopTime, " *** \r\n")

if __name__ == "__main__":

    main()
    
