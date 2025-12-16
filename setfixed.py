"""Compatibility wrapper.

This module provides a thin wrapper function `set_controller_fixed_ip` that
delegates to `Licel.licel_tcpip.EthernetController.set_controller_fixed_ip`.
Callers may use this wrapper or call the method directly on an
`EthernetController` instance.
"""
from __future__ import annotations

from typing import Tuple

from Licel.licel_tcpip import EthernetController


def set_controller_fixed_ip(old_ip: str,
                            old_port: int,
                            new_ip: str,
                            mask: str,
                            new_port: int,
                            gateway: str,
                            passwd: str,
                            dry_run: bool = False) -> Tuple[bool, str]:
    """Delegate to `EthernetController.set_controller_fixed_ip`.

    This keeps backwards compatibility for external callers.
    """
    ec = EthernetController(old_ip, int(old_port))
    # If dry_run, do not open network connection — return the command directly.
    if dry_run:
        cmd = f'TCPIP "{new_ip}" "{mask}" "{gateway}" "{new_port}" "{passwd}"'
        return True, cmd

    # Open connection, call method, then ensure connection is closed.
    try:
        ec.openConnection()
        ok, resp = ec.set_controller_fixed_ip(new_ip=new_ip, mask=mask, new_port=new_port, gateway=gateway, passwd=passwd)
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
        prog='setfixed',
        description='Set a Licel controller fixed IP address via TCPIP command')
    parser.add_argument('oldip', help='current IP address of the controller')
    parser.add_argument('oldport', type=int, help='current control port of the controller')
    parser.add_argument('newip', help='new IP address to set on the controller')
    parser.add_argument('newport', type=int, help='new port the controller will use after reboot')
    parser.add_argument('mask', help='subnet mask for the controller (e.g. 255.255.255.0)')
    parser.add_argument('gateway', help='gateway address for the controller')
    parser.add_argument('passwd', help='controller password')
    parser.add_argument('--dry-run', action='store_true', help='print the TCPIP command without sending it')
    args = parser.parse_args()

    try:
        ok, resp = set_controller_fixed_ip(args.oldip, args.oldport, args.newip, args.mask, args.newport, args.gateway, args.passwd, dry_run=args.dry_run)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(2)

    if args.dry_run:
        print(resp)
        sys.exit(0)

    if ok:
        print("Switch controller off and on again to activate new IP address")
        print(resp)
        sys.exit(0)
    else:
        print("Set fixed IP address failed")
        print(resp)
        sys.exit(1)
