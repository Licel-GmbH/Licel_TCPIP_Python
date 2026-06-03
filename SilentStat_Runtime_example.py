import argparse
from Licel import licel_tcpip

'''
This script changes the SilentStat delay configuration at runtime and
can activate or deactivate the SilentStat feature.
The pre-trigger and post-trigger block delay times are applied directly
to the controller without saving them to flash memory.
The default state (on or off) after a controller reboot will remain unchanged.
This feature is only supported by controllers with IDN containing "Silent".

'''

DEFAULT_IP   = "10.49.234.234"
DEFAULT_PORT = 2055


def commandLineInterface():
    parser = argparse.ArgumentParser(description="Control the SilentStat feature of a Licel Ethernet Controller.")
    parser.add_argument("--ip",   type=str, default=DEFAULT_IP,   help="Controller IP address (default: %(default)s)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Controller port (default: %(default)s)")
    parser.add_argument("--preTrigDelay",  type=int, metavar="US",  help="Pre-trigger block delay in microseconds (optional)")
    parser.add_argument("--postTrigDelay", type=int, metavar="US",  help="Post-trigger block delay in microseconds (optional)")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--on",  action="store_true", help="Activate the silent stat")
    group.add_argument("--off", action="store_true", help="Deactivate the silent stat")

    args = parser.parse_args()

    if (args.preTrigDelay is None) != (args.postTrigDelay is None):
        parser.error("--preTrigDelay and --postTrigDelay must both be specified together")

    return args


def main():
    myArguments = commandLineInterface()
    ip   = myArguments.ip
    port = myArguments.port
    preTriggerDelay = myArguments.preTrigDelay
    postTriggerDelay = myArguments.postTrigDelay

    ethernetController = licel_tcpip.EthernetController(ip, port)
    ethernetController.openConnection()

    if preTriggerDelay is not None and postTriggerDelay is not None:
        print(ethernetController.SilentStat.setDelay(int(preTriggerDelay), int(postTriggerDelay)))
        preTrig, postTrig = ethernetController.SilentStat.getDelay()
        print("Pre-trigger delay  :", preTrig,  "us")
        print("Post-trigger delay :", postTrig, "us")


    if myArguments.on:
        print(ethernetController.SilentStat.ON())
    elif myArguments.off:
        print(ethernetController.SilentStat.OFF())

    print("State :", ethernetController.SilentStat.getState())

    ethernetController.shutdownConnection()


if __name__ == "__main__":
    main()