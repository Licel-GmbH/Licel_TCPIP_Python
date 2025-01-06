from Licel import  licel_tcpip, photomultiplier
import argparse
import time



def commandLineInterface():
    argparser = argparse.ArgumentParser(description='photomultiplier example ')
    argparser.add_argument('--ip', type=str, default = "10.49.234.234",
                            help='ethernet controller ip address')
    argparser.add_argument('--port', type=int, default=2055,
                            help='ethernet controller command port')
    argparser.add_argument('--PMT', type=int, default=0,
                            help='PMT number to communicate with')
    argparser.add_argument('--voltage', type=int,  default=0,
                            help="desired voltage in Volt.")

    args = argparser.parse_args()
    return args
 
def main():
    
    #initialize acquisition parameters using parameters passed from command line interface
    myArguments = commandLineInterface()    
    ip = myArguments.ip
    port = myArguments.port
    pmt_device_number = myArguments.PMT
    voltage = myArguments.voltage


    ethernetController = licel_tcpip.EthernetController (ip, port)
    pmt = photomultiplier.photomultiplier(ethernetController)

    ethernetController.openConnection()
    ethernetController.getID()
    print(ethernetController.getCapabilities())

    print("*** Listing installed PMT's *** \r\n")
    print(pmt.listInstalledPMT())
    print("\r\n*** Setting PMT number",pmt_device_number, "to", voltage, "Volt *** \r\n")
    print(pmt.setHV(pmt_device_number,voltage))
    print("\r\n*** Get PMT", pmt_device_number, "voltage *** \r\n")
    print(pmt.getHV(pmt_device_number))
    print("\r\n*** Setting PMT number", pmt_device_number, "to 0 Volt *** \r\n")
    print(pmt.setHV(pmt_device_number,0))

    ethernetController.shutdownConnection()

if __name__ == "__main__":
    main()