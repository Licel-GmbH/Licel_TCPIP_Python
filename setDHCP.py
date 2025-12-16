"""Wrapper to activate DHCP on a Licel Ethernet controller.

This module uses only `Licel.licel_tcpip.EthernetController` to open the
connection, send the DHCP command, and close the connection.

It mirrors the behavior and command syntax of the C utility in
`Licel_TCPIP/setDHCP_src` (uses `TCPIP "DHCP" "<port>" "<passwd>"`).
"""
from __future__ import annotations

from typing import Tuple
from Licel.licel_tcpip import EthernetController


def set_controller_dhcp(old_ip: str, old_port: int, new_port: int, passwd: str, dry_run: bool = False) -> Tuple[bool, str]:
    """Set the controller into DHCP mode.

    - `old_ip`, `old_port`: address to connect to the controller
    - `new_port`: port the controller should use after reboot
    - `passwd`: controller password
    - `dry_run`: if True, returns the command without opening a connection

    Returns (success, response_or_command)
    """
    ec = EthernetController(old_ip, int(old_port))
    cmd = f'TCPIP "DHCP" "{new_port}" "{passwd}"'
    if dry_run:
        return True, cmd

    try:
        ec.openConnection()
        ok, resp = ec.activate_dhcp(new_port, passwd)
    finally:
        try:
            ec.shutdownConnection()
        except Exception:
            pass
    return ok, resp


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog='setDHCP',
        description='Activate DHCP mode on a Licel controller via TCPIP command')
    parser.add_argument('oldip', help='current IP address of the controller')
    parser.add_argument('oldport', type=int, help='current control port of the controller')
    parser.add_argument('newport', type=int, help='new port the controller will use after reboot')
    parser.add_argument('passwd', help='controller password')
    parser.add_argument('--dry-run', action='store_true', help='print the TCPIP command without sending it')
    args = parser.parse_args()

    try:
        ok, resp = set_controller_dhcp(args.oldip, args.oldport, args.newport, args.passwd, dry_run=args.dry_run)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(2)

    if args.dry_run:
        print(resp)
        sys.exit(0)

    if ok:
        print(resp)
        print("Switch controller off and on again to activate DHCP Mode")
        sys.exit(0)
    else:
        print('Activate DHCP failed')
        print(resp)
        sys.exit(1)
