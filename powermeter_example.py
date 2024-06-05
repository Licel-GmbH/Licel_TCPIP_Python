'''
Copyright ©: Licel GmbH

python3 powermeter_example.py --ip <ip> --port <port>  --acq <num acquis> --channel <channel>
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

    args = argparser.parse_args()
    return args
 
def main():
        
    #initialize acquisition parameters using parameters passed from command line interface
    myArguments = commandLineInterface()    
    ip = myArguments.ip
    port = myArguments.port
    ACQUISTION_CYCLES = myArguments.acq
    channel = myArguments.channel

    ethernetController = licel_tcpip.licelTCP (ip, port)
    Powermeter = powermeter.powermeter(ethernetController)

    ethernetController.openConnection()
    ethernetController.openPushConnection()

    ethernetController.getID()
    print(ethernetController.getCapabilities())
    print(Powermeter.selectChannel(channel))

    print("*** Start acquiring pulse amplitude *** \r\n")
    print(Powermeter.Start())
    for i in range (0, ACQUISTION_CYCLES):
        print(Powermeter.readPushLine())
    
    print("*** Stop acquiring pulse amplitude *** \r\n")
    print(Powermeter.Stop())

    print("*** Acquire single trace *** \r\n")
    print(Powermeter.getTrace())

    ethernetController.shutdownPushConnection()
    ethernetController.shutdownConnection()

if __name__ == "__main__":
    main()