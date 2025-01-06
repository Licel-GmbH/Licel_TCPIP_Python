'''
Copyright ©: Licel GmbH

python3 powermeter_example.py --ip <ip> --port <port>  --acq <num acquis>
                              --channel <channel>  --internalTrigger
'''

from Licel import  licel_tcpip, powermeter
import argparse


def commandLineInterface():
    argparser = argparse.ArgumentParser(description='Powermeter example')
    argparser.add_argument('--ip', type=str, default = "10.49.234.234",
                            help='ethernet controller ip address')
    argparser.add_argument('--port', type=int, default=2055,
                            help='ethernet controller command port')
    argparser.add_argument('--acq', type=int, default=100,
                            help='number of acquisitions')
    argparser.add_argument('--channel', type=int,  default=0,
                            help=("Selects the ADC channel for the data acquisition." 
                            "channel can either be 0 for photodiode, 2 for powermeter."))
    argparser.add_argument('--internalTrigger', type=bool, default=False,
                           action=argparse.BooleanOptionalAction,
                           help='activate the internal trigger')
    args = argparser.parse_args()
    return args
 
def main():
        
    #initialize acquisition parameters using parameters passed from command line interface
    myArguments = commandLineInterface()    
    ip = myArguments.ip
    port = myArguments.port
    ACQUISTION_CYCLES = myArguments.acq
    channel = myArguments.channel
    SimTrig = myArguments.internalTrigger

    ethernetController = licel_tcpip.EthernetController (ip, port)
    Powermeter = powermeter.powermeter(ethernetController)

    ethernetController.openConnection()
    ethernetController.openPushConnection()

    print(ethernetController.getID())
    capability = ethernetController.getCapabilities()
    print(capability)
    if capability.find('POW') == -1 :
        raise RuntimeError("Missing capabilities POW")

    print(Powermeter.selectChannel(channel))
    
    print("*** get number number of triggers ***")
    print(Powermeter.getNumberOfTrigger())
    
    if (SimTrig):
        print("*** Start internal Trigger ***")
        print(Powermeter.startInternalTrigger())

    print("*** Start acquiring pulse amplitude *** \r\n")
    print(Powermeter.Start())
    for i in range (0, ACQUISTION_CYCLES):
        timestamp, pulseAmplitude, trigger_num = Powermeter.getPowermeterPushData()
        formattedData = ("Pulse amplitude = {}, "
                         "controller timestamp {} ms, "
                         "trigger number {} \r\n"
                          .format(pulseAmplitude, timestamp, trigger_num))
        print(formattedData)
    
    print("*** Stop acquiring pulse amplitude *** \r\n")
    print(Powermeter.Stop())


    print("*** Acquire single trace *** \r\n")
    singleTraceData = Powermeter.getTrace()
    print(singleTraceData)

    if (SimTrig):
        print("*** Stop internal Trigger ***")
        print(Powermeter.stopInternalTrigger())



    ethernetController.shutdownPushConnection()
    ethernetController.shutdownConnection()

if __name__ == "__main__":
    main()