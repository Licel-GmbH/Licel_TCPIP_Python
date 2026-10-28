'''
Copyright ©: Licel GmbH

Configure the analog signal trigger (overflow detection) of a transient recorder.

python3 TR_overflowDetection_example.py --ip <ip> --port <port> --TR <tr number> --level <level in LSB>
        --start <start in us> --stop <stop in us> --timeout <timeout in ms> --block <block in ms>
'''
from Licel import licel_tcpip
import argparse


def commandLineInterface():
    argparser = argparse.ArgumentParser(description='signal trigger example')
    argparser.add_argument('--ip', type=str, default="10.49.234.234",
                            help='ethernet controller ip address')
    argparser.add_argument('--port', type=int, default=2055,
                            help='ethernet controller command port')
    argparser.add_argument('--TR', type=int, default=0,
                            help='transient recorder number to communicate with')
    argparser.add_argument('--level', type=int, required=True,
                            help='trigger level in LSB')
    argparser.add_argument('--start', type=float, required=True,
                            help='start of the detection window in us')
    argparser.add_argument('--stop', type=float, required=True,
                            help='stop of the detection window in us')
    argparser.add_argument('--timeout', type=float, required=True,
                            help='timeout in ms')
    argparser.add_argument('--block', type=float, required=True,
                            help='block time in ms')

    args = argparser.parse_args()
    return args

def main():

    myArguments = commandLineInterface()

    ethernetController = licel_tcpip.EthernetController(myArguments.ip, myArguments.port)
    ethernetController.openConnection()
    print(ethernetController.getID())

    print(ethernetController.Tr.selectTR(myArguments.TR))
    print(ethernetController.Tr.setOverflowInformation(myArguments.level,
                                                       myArguments.start,
                                                       myArguments.stop,
                                                       myArguments.timeout,
                                                       myArguments.block))

    ethernetController.shutdownConnection()

if __name__ == "__main__":
    main()
