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
                    help='number of acquisitions, if -1 we will acquire infinite number of acquisitions')
    argparser.add_argument('--shots', type=int,  default=150,
                    help='number of shots per acquisition')
    argparser.add_argument('--log', type=bool, default=False,
                           action=argparse.BooleanOptionalAction,
                    help='log the push data when error occurs in push buffer raw data ')
    argparser.add_argument('--acquis_per_file', type=int, nargs='?', default=10,
                    help='maximal number of acquisitions to write in a single file')
    
    args = argparser.parse_args()
    return args 

#initialize acquisition parameters using parameters passed from command line interface
myArguments = commandLineInterface()
ip = myArguments.ip
port = myArguments.port
desiredShots = myArguments.shots
ACQUISTION_CYCLES = myArguments.acq
ACQUISPERFILE = myArguments.acquis_per_file 
LOGPUSHDATA = myArguments.log 

def singleAcquistionCycle(ethernetController, dataParser,
                           ConfigInfo):
    
    startTime =  datetime.now()
    ethernetController.recvPushData() 
    stopTime =  datetime.now()

    if (LOGPUSHDATA): 
        controllerTimeMs = ethernetController.getMilliSecs()
        Idn = ethernetController.getID()
        dataParser.pushDataLog(logFilePath,
                                ethernetController,
                                Idn,
                                startTime,
                                ConfigInfo)
    (dataValid,
     dataSets,
     time_stamp,
     analogue_shots,
     pc_shots) = dataParser.parseDataFromBuffer(ConfigInfo,
                                                ethernetController,
                                                desiredShots)
    
    if (dataValid): 
        dataParser.savePushDataToLicelFileFormat(dataSets,
                                      ConfigInfo,
                                      startTime,stopTime,
                                      ethernetController.hardwareInfos,
                                      time_stamp,
                                      analogue_shots, 
                                      pc_shots,
                                      desiredShots,
                                      ACQUISPERFILE ) 

    else :
        # if data is not valid clear buffer until next occurrence of xff xff 
        dataParser.removeInvalidDataFromBuffer(ethernetController.pushBuffer)

def main():
    
    ethernetController = licel_tcpip.EthernetController (ip, port)
    dataParser = licel_data.DataParser()
    ConfigInfo = licel_Config.Config("Acquis.ini")
    
    ConfigInfo.readConfig()
    ethernetController.openConnection()
    ethernetController.openPushConnection()

    print(ethernetController.listInstalledTr())   
    ethernetController.configureHardware(ConfigInfo)
    print(ethernetController.MPushStartFromConfig(desiredShots, ConfigInfo))
    startTime =  datetime.now()
    print("*** Started mpush acqusition at:",startTime, " *** \r\n")

    cycle_count = 0
    while ((cycle_count < ACQUISTION_CYCLES) or (ACQUISTION_CYCLES == -1) ):
        try:
            cycle_count += 1
            singleAcquistionCycle(ethernetController, dataParser, ConfigInfo)
        except (ConnectionError, ConnectionResetError, TimeoutError) as myExecption:
            cycle_count = cycle_count - 1
            ethernetController.reconnection(ConfigInfo)
            print("*** Restarting MPUSH *** ")
            print(ethernetController.MPushStartFromConfig(desiredShots, ConfigInfo))
        except KeyboardInterrupt: 
            print("User interrupted program by pressing Ctrl-C.")
            break


    ethernetController.MPushStop()
    ethernetController.shutdownConnection()
    ethernetController.shutdownPushConnection()
    stopTime =  datetime.now()
    print("{} acquisition written to {} \r\n"
        .format(cycle_count, ConfigInfo.measurmentInfo.szOutPath))
    print("*** Stopped mpush acquisition at:",stopTime, " *** \r\n")

if __name__ == "__main__":

    main()
    
