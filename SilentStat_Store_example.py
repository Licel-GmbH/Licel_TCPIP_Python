import argparse
from Licel import licel_tcpip

'''
This script permanently saves the current SilentStat configuration
(on/off state and pre-/post-trigger block delay times) to the
controller's flash memory.
After a reboot the controller will restore these stored settings
as the new default. A password is required to authorize the store operation.
This feature is only supported by controllers with IDN containing "Silent".
'''

DEFAULT_IP   = "10.49.234.234"
DEFAULT_PORT = 2055


def commandLineInterface():
    parser = argparse.ArgumentParser(description="Control the SilentStat feature of a Licel Ethernet Controller.")
    parser.add_argument("--ip",   type=str, default=DEFAULT_IP,   help="Controller IP address (default: %(default)s)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Controller port (default: %(default)s)")
    parser.add_argument("--password", type=str, required=True, help="Password for storing configuration, Default password is 'Administrator'")

    args = parser.parse_args()

    return args


def main():
    myArguments = commandLineInterface()
    ip   = myArguments.ip
    port = myArguments.port
    password = myArguments.password

    ethernetController = licel_tcpip.EthernetController(ip, port)
    ethernetController.openConnection()

    print("Current SilentStat configuration:")
    preTrig, postTrig = ethernetController.SilentStat.getDelay()
    print("  State :", ethernetController.SilentStat.getState())
    print("  Pre-trigger delay  :", preTrig,  "us \r\n")
    print("  Post-trigger delay :", postTrig, "us \r\n")
    print("Storing configuration to flash memory... \r\n")
    print(ethernetController.SilentStat.store(password))

    ethernetController.shutdownConnection()


if __name__ == "__main__":
    main()